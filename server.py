import socket
import threading
import os
from string import punctuation
import random
import re
import logging

import chatlogic
import helpers

LOGFILE = './log/server.log'
config = helpers.get_config()
toBool = lambda str: True if str == "True" else False 

DEBUG_SERVER = toBool(config["DEBUG"]["server"])
LOGGING_FMT = '%(asctime)s %(threadName)s %(message)s'

regexpYes = re.compile(r'yes')

if DEBUG_SERVER:
    logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format=LOGGING_FMT)
else:
    logging.basicConfig(filename=LOGFILE, level=logging.INFO, format=LOGGING_FMT)

def session(connection):
    # Get Config
    conf = helpers.get_config()
    DBHOST = conf["MySQL"]["server"] 
    DBUSER = conf["MySQL"]["dbuser"]
    DBNAME = conf["MySQL"]["dbname"]
    
    logging.info("Starting Bot session-thread...") 

    # Initialize the database connection
    logging.info("   session-thread connecting to database...")
    dbconnection = helpers.db_connection(DBHOST, DBUSER, DBNAME)
    dbcursor =  dbconnection.cursor()
    dbconnectionid = helpers.db_connectionid(dbcursor)
    logging.info("   ...connected")
    
    botSentence = 'Hello!'
    weight = 0
    
    trainMe = False
    checkStore = False
    
    def receive(connection):
        
        logging.debug("   receive(connection): PID {}, thread {} \n".format(pid, thread))
        received = connection.recv(1024)
        if not received:
            return False
        else:
            return received
   
    while True:
        pid = os.getpid()
        thread = threading.current_thread()
        
        # pass received message to chatbot
        received = receive(connection)
        humanSentence = received.decode().strip()
        
        if humanSentence == '' or humanSentence.strip(punctuation).lower() == 'quit' or humanSentence.strip(punctuation).lower() == 'exit':
            break

        # Chatbot processing
        botSentence, weight, trainMe, checkStore = chatlogic.chat_flow(dbcursor, humanSentence, weight)
        logging.debug("   Received botSentence {} from chatbot.chat_flow".format(botSentence))
        
        if trainMe:
            logging.debug("   trainMe is True")
            send = "Please train me by entering some information for me to learn, or reply \"skip\" to skip' ".encode()
            connection.send(send)
            previousSentence = humanSentence
            received = receive(connection)
            humanSentence = received.decode().strip()
            logging.debug("   trainMe received {}".format(humanSentence))
                        
            if humanSentence != "skip":
                chatlogic.train_me(previousSentence, humanSentence, dbcursor)
                botSentence = "Thanks I have noted that"
            else:
                botSentence = "OK, moving on..."
                trainMe = False
                
        if checkStore:
            logging.debug("CheckStore is True")
            send = 'Shall I store this information as a fact for future reference?  (Reply "yes" to store)'.encode()
            connection.send(send)
            previousSentence = humanSentence
            received = receive(connection)
            humanSentence = received.decode().strip()
            logging.debug("   checkStore received {}".format(humanSentence))
            
            if regexpYes.search(humanSentence.lower()):
                #Store previous Sentence
                logging.debug("   Storing...")
                chatlogic.store_statement(previousSentence, dbcursor)
                logging.debug("   Statement Stored.")
                botSentence = random.choice(chatlogic.STATEMENT_STORED)
            else:
                botSentence = "OK, moving on..."
                checkStore = False

        dbconnection.commit()
        logging.debug("   sending botSentence back: {}".format(botSentence))
        send = botSentence.encode()

        connection.send(send)
    logging.info("   Closing Session")

if __name__ == "__main__":
    logging.info("-----------------------------")
    logging.info("--  Starting the BotServer     --")
    print("Starting the Server...")
    print("Logging to: ", LOGFILE)
    
    LISTEN_HOST = config["Server"]["listen_host"]
    LISTEN_PORT = int(config["Server"]["tcp_socket"])
    LISTEN_QUEUE = int(config["Server"]["listen_queue"])
    
    # Set up the listening socket
    sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    sckt.bind((LISTEN_HOST, LISTEN_PORT))
    sckt.listen(LISTEN_QUEUE)
    print("...Socket has been set up")
    logging.info("Server Listener set up on port " + str(LISTEN_PORT))
    
    # Accept connections in a loop
    while True:
        logging.info("Main Server waiting for a connection")
        (connection, address) = sckt.accept()
        logging.info("Connect Received " + str(connection) + " " + str(address))
        t = threading.Thread(target = session, args=[connection])
        t.setDaemon(True)  #set to Daemon status, allows CTRL-C to kill all threads
        t.start()
    
    logging.info("Closing Server listen socket on " + str(LISTEN_PORT))
    sckt.close()
       
