#!/usr/bin/python
import os
import re
import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
import sys
import getopt
import math
from xmlparser import XMLParser
try:
   import cPickle as pickle
except:
   import pickle


TUPLE_DOC_ID = 0
TUPLE_POS_ARR = 1

pointerDict = {} # stores the byte pointers for each term's posting array in the collection
postingDict = {} # stores posting array for each term in collection
docDict = {} # stores the raw length of each document in the collection
currentDocId = 0
numberOfDocumentsToRead = 2

xmlparser = XMLParser()

# Remove punctuations
# tokenize according to words
# go through every word, if new, add to dictionary, and create a new array with its Doc ID inside --> Create new entry for freq dictionary, +1
#                       if not, find the old dict array, check if the last element is current docID, if nt then append new entry --> +1 for freq dict
# 
def readFilesInDirectory(directory):
    global currentDocId
    global totalNumOfDocs
    global docDict

    listOfDir = os.listdir(directory)
    totalNumOfDocs = len(listOfDir)

    # Go through every file in the given directory
    for filename in listOfDir:

        # Retrieve File
        file = os.path.join(directory, filename)

        # Update currentDocId for reference later
        currentDocId = int(filename)

        # Create new entry for docLengthDict
        docDict[currentDocId] = 0

        # Index the file
        indexDoc(file)

# Current Main Method, for testing purposes, only index small portion of library
def readSomeFilesInDirectory(directory):
    global currentDocId
    global docDict

    totalNumOfDocs = numberOfDocumentsToRead
    filenameArray = os.listdir(directory)

    for i in range(0, numberOfDocumentsToRead):

        # Get filename and file full directory
        filename = filenameArray[i]
        file = os.path.join(directory, filename)

        # Update currentFilename for reference later
        currentDocId = int(filename.split('.')[0])

        # Create new entry for docLengthDict
        docDict[currentDocId] = 0

        indexDoc(file) 
    
    # for doc, length in docDict.iteritems():
    # print(doc, length)
    

def stem_tokens(tokens, stemmer):
    return [stemmer.stem(token) for token in tokens]

# Combines tokens for contracted words that were previously
# split due to word_tokenize
def combine_contracted(words):
    
    # Returns input array if it does not have more than 2 elements
    if len(words) < 2:
        return words

    # Loop through all adjacnt word pairs
    combinedWords = []
    for i in range(0, len(words) - 1):
        j = i + 1
        firstWord = words[i]
        secondWord = words[j]

        # If second word contains aprostrophe (eg. 's), then combine
        # and assign to words[i], leave words[j] as empty string
        if "'" in secondWord:
            words[i] = firstWord + secondWord
            words[j] = ' '

    # Remove all entries with ''
    for word in words:
        if word != ' ':
            combinedWords.append(word)

    return combinedWords 


def indexDoc(file):
    global xmlparser
    global docDict

    # Parse document using xmlparser
    xmlparser.parseDoc(file)

    # --- Index Contents ---
    indexZone("content", xmlparser.contentStr)

    # --- Index other zones ---
    indexZone("title", xmlparser.titleStr)
    indexZone("source_type", xmlparser.sourceStr)
    indexZone("content_type", xmlparser.contentType)
    indexZone("court", xmlparser.court)
    indexZone("domain", xmlparser.domain)

    # --- Store document properties ---
    if currentDocId not in docDict:
        docDict[currentDocId] = {
                                "length" : 0,
                                "jurisdiction": xmlparser.jurisdictionArr,
                                "tag": xmlparser.tagArr,
                                "areaoflaw": xmlparser.areaOfLawArr,
                                "date": xmlparser.date
                                }
    else:
        docDict[currentDocId].update({
                                "jurisdiction": xmlparser.jurisdictionArr,
                                "tag": xmlparser.tagArr,
                                "areaoflaw": xmlparser.areaOfLawArr,
                                "date": xmlparser.date
                                })

    print "indexed", currentDocId

def indexZone(zone, zoneString):
    global docDict

    # Setup stemmer
    stemmer = PorterStemmer()

    # Convert into a single string
    zoneString.replace('\n', '')
    zoneString = re.sub(ur"[^\w\d'\s\-]+", '', zoneString)
    zoneString.replace('/', ' ')
        
    # Tokenize string into array of words
    words = word_tokenize(zoneString)

    # Combine contracted words if any
    words = combine_contracted(words)

    # Stem tokens
    words = stem_tokens(words, stemmer)
    
    # Case Folding
    caseFoldedArray = []
    for word in words:
        caseFoldedArray.append(word.lower())

    # Index each word
    pos = 0
    for word in caseFoldedArray:
        indexWord(word, zone, pos)
        pos += 1

    if zone == "content":
        # Store doc raw length
        docDict[currentDocId] = {"length": len(caseFoldedArray)}

def indexWord(word, zone, pos):
    global postingDict

    wordWithZone = zone + "." + word
    print wordWithZone
    # Newly encountered word
    if wordWithZone not in postingDict:
        # Create Dict entry and posting list
        postingsList = [(currentDocId, [pos])] # Tuple: (posting, [posArr])
        postingDict[word] = postingsList

    else:
        # Check if currentDocId already registered in posting list.
        postingsList = postingDict[word]
        if postingsList[-1][TUPLE_DOC_ID] != currentDocId:

            # Add new entry if it does not exist
            postingsList.append((currentDocId, [pos]))
        
        # If currentDocId already exists, append the new positional index
        else :
            existingTuple = postingsList[-1]
            newTuple = (existingTuple[0], existingTuple[1].append(pos))
            postingsList[-1] = newTuple

def generateDictionaryAndPostingsFile(dictionary_file, postings_file):
    global pointerDict

    pointerDict = {}
    fp = open(postings_file, "wb")

    # Create postings_file
    for word in postingDict:

        # Store f.tell() as start index for this word, then write as bytearray to file
        pointerDict[word] = fp.tell()
        postingsArray = postingDict[word]
        pickle.dump(postingsArray, fp)

    fp.close()

    # write docDict and pointerDict to dictionary_file
    fd = open(dictionary_file, "wb")
    dictOfDictionaries = {"doc": docDict, "pointer": pointerDict}
    pickle.dump(dictOfDictionaries, fd)
    fd.close()

# FOR DEBUG
def readPostings(postings_file, word):
    index = pointerDict.get(word, None)

    if index == None:
        array = []
    else:
        f = open(postings_file, "rb")
        f.seek(index)
        array = pickle.load(f)

    return array

# FOR DEBUG
def readDictionaries(dictionary_file):
    f = open(dictionary_file, "rb")
    dictOfDictionaries = pickle.load(f)

    pointerDict = dictOfDictionaries["pointer"]
    for key, value in pointerDict.iteritems() :
       print key, value

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"

# Handle run
input_file_i = input_file_d = input_file_p = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-i':
        input_file_i = a
    elif o == '-d':
        input_file_d = a
    elif o == '-p':
        input_file_p = a
    else:
        assert False, "unhandled option"
if input_file_i == None or input_file_d == None or input_file_p == None:
    usage()
    sys.exit(2)

# main program
#readFilesInDirectory(input_file_i)
readSomeFilesInDirectory(input_file_i)
generateDictionaryAndPostingsFile(input_file_d, input_file_p)
#readDictionaries(input_file_d)

# Sample run commandline for my local comp
# python index.py -i "/Users/jane/nltk_data/corpora/reuters/training/" -d "dictionary.txt" -p "postings.txt"
