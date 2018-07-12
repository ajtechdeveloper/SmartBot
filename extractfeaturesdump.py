##################################################################
# Use the extractfeatures.py file to dump out features
# Read a CSV of sentences and bulk-dump to featuresDump.csv of features
##################################################################

#Input CSV fmt:  1st field is sentence ID, 2nd field is text to process, 3rd field is class

import csv
import sys
import hashlib

import extractfeatures # extractfeatures.py is bepoke util to extract NLTK POS features from sentences

if len(sys.argv) > 1:
    FNAME = sys.argv[1]
else:
    FNAME = './data/classifySentences.csv'
print("reading input from ", FNAME)


if len(sys.argv) > 2:
    FOUT = sys.argv[2]
else:
    FOUT = './dumps/featuresDump.csv'
print("Writing output to ", FOUT)

fin = open(FNAME, 'rt')
fout = open(FOUT, 'wt', newline='')

keys = ["id",
"wordCount",
"stemmedCount",
"stemmedEndNN",
"CD",
"NN",
"NNP",
"NNPS",
"NNS",
"PRP",
"VBG",
"VBZ",
"startTuple0",
"endTuple0",
"endTuple1",
"endTuple2",
"verbBeforeNoun",
"qMark",
"qVerbCombo",
"qTripleScore",
"sTripleScore",
"class"]

reader = csv.reader(fin)

loopCount = 0
next(reader)  #Assume we have a header 
for line in reader:
    sentence = line[0]  
    c = line[1]        #class-label
    id = hashlib.md5(str(sentence).encode('utf-8')).hexdigest()[:16] # generate a unique ID
    
    output = ""  
    header = ""

    f = extractfeatures.features_dict(id,sentence, c)
     
    for key in keys:
        value = f[key]
        header = header + ", " + key 
        output = output + ", " + str(value)

    if loopCount == 0:   # only extract and print header for first dict item
        header = header[1:]               #strip the first ","" off
        print(header)
        fout.writelines(header + '\n')
    
    output = output[1:]               #strip the first ","" off
    
    loopCount = loopCount + 1            
    print(output)
    fout.writelines(output + '\n')
        

fin.close()
fout.close()