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
from datetime import datetime
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
stemmingDictionary = {} # Cache to quicken stemming
totalNumOfDocs = 0
currentDocId = 0
numberOfDocumentsToRead = 10

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
    docIndexed = 0

    start = datetime.now()
    print "indexing..."
    for filename in listOfDir:

        # Retrieve File
        file = os.path.join(directory, filename)

        # Ignore iOS stuffs
        if filename == ".DS_Store":
            continue

        # Update currentDocId for reference later
        currentDocId = int(filename.split('.')[0])

        # Create new entry for doc
        docDict[currentDocId] = 0

        # Index the file
        indexDoc(file)

        # Log Progress
        docIndexed += 1
        print '{0}/{1} indexed\r'.format(docIndexed, totalNumOfDocs)

    end = datetime.now()
    print "Index Complete. Time taken:", (end-start).total_seconds()

# Current Main Method, for testing purposes, only index small portion of library
def readSomeFilesInDirectory(directory):
    global currentDocId
    global docDict
    global totalNumOfDocs

    totalNumOfDocs = numberOfDocumentsToRead
    filenameArray = os.listdir(directory)

    start = datetime.now()
    print "indexing..."
    docIndexed = 0
    for i in range(0, numberOfDocumentsToRead):

        # Get filename and file full directory
        filename = filenameArray[i]
        file = os.path.join(directory, filename)

        # Ignore iOS stuffs
        if filename == ".DS_Store":
            continue

        # Update currentFilename for reference later
        currentDocId = int(filename.split('.')[0])

        # Create new entry for doc
        docDict[currentDocId] = 0

        indexDoc(file) 
        # Log Progress
        docIndexed += 1
        print '{0}/{1} indexed\r'.format(docIndexed, totalNumOfDocs)
    
    end = datetime.now()
    print "Index Complete. Time taken:", (end-start).total_seconds()

def stem_tokens(tokens, stemmer):
    global stemmingDictionary

    result = []
    for token in tokens:
        # Look for cache
        cache = stemmingDictionary.get(token, None)
        if cache is not None:
            result.append(cache)
            continue
        # Else, stem and update cache
        try:
            stem = stemmer.stem(token)
            result.append(stem)
            stemmingDictionary[token] = stem
        except:
            print token, "cannot be stemmed"
            result.append(token)
            stemmingDictionary[token] = token

    return result

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

    start = datetime.now()
    # Parse document using xmlparser
    xmlparser.parseDoc(file)

    # --- Prepare doc entry ---
    docDict[currentDocId] = {}

    # --- Index Content ---
    indexZone("content", xmlparser.contentStr)

    # --- Preprocess Metadata ---
    tagArr = []
    for tag in xmlparser.tagArr:
        processedTag = preprocessText(tag)
        tagArr.append(processedTag)
    areaOfLawArr = []
    for area in xmlparser.areaOfLawArr:
        processedArea = preprocessText(area)
        areaOfLawArr.append(processedArea)

    # --- Store document properties ---
    docDict[currentDocId].update({
                            "source_type": xmlparser.sourceStr,
                            "content_type": xmlparser.contentType,
                            "court": xmlparser.court,
                            "domain": xmlparser.domain,
                            "jurisdiction": xmlparser.jurisdictionArr,
                            "tag": tagArr,
                            "areaoflaw": areaOfLawArr,
                            "date": xmlparser.date
                            })

def indexZone(zone, zoneString):
    global docDict

    # Preprocess zone string to array of words
    words = preprocessText(zoneString)

    # Index each word
    lengthDict = {}
    pos = 0
    for word in words:
        indexWord(word, zone, pos)
        pos += 1
        length = lengthDict.get(word, 0)
        lengthDict[word] = length + 1

    # Index content zone length for length normalisation
    if zone == "content":
        zoneLength = 0
        for word in lengthDict.keys():
            zoneLength += math.pow(lengthDict[word], 2)

        zoneLength = math.sqrt(zoneLength) 
        entry = "contentlength"
        docDict[currentDocId].update({entry: zoneLength})

def indexWord(word, zone, pos):
    global postingDict

    wordWithZone = zone + "." + word
    # Newly encountered word
    if wordWithZone not in postingDict:
        # Create Dict entry and posting list
        postingsList = [(currentDocId, [pos])] # Tuple: (posting, [posArr])

    else:
        # Check if currentDocId already registered in posting list.
        postingsList = postingDict[wordWithZone]
        if postingsList[-1][TUPLE_DOC_ID] != currentDocId:

            # Add new entry if it does not exist
            postingsList.append((currentDocId, [pos]))
        
        # If currentDocId already exists, append the new positional index
        else :
            existingTuple = postingsList[-1]
            existingTuple[TUPLE_POS_ARR].append(pos)
            postingsList[-1] = existingTuple
            
    postingDict[wordWithZone] = postingsList

# Preprocess Input:
# + punctuation removal 
# + tokenization 
# + stemming 
# + case folding
def preprocessText(rawText):

     # Setup stemmer
    stemmer = PorterStemmer()

    # Convert into a single string
    rawText.replace('\n', '')
    rawText = re.sub(ur"[^\w\d'\s\-]+", '', rawText)
    rawText.replace('/', ' ')
        
    # Tokenize string into array of words
    words = word_tokenize(rawText)

    # Combine contracted words if any
    words = combine_contracted(words)

    # Stem tokens
    words = stem_tokens(words, stemmer)
    
    # Case Folding
    caseFoldedArray = []
    for word in words:
        caseFoldedArray.append(word.lower())

    return caseFoldedArray

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
    dictOfDictionaries = {"document": docDict, "pointer": pointerDict, "collection": totalNumOfDocs}
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

# Main Program
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
readFilesInDirectory(input_file_i)
#readSomeFilesInDirectory(input_file_i)
generateDictionaryAndPostingsFile(input_file_d, input_file_p)
#readDictionaries(input_file_d)

# Sample run commandline for my local comp
# python index.py -i "/Users/jane/nltk_data/corpora/reuters/training/" -d "dictionary.txt" -p "postings.txt"
