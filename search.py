#!/usr/bin/python
import re
import os
import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
import sys
import getopt
import math
import heapq
try:
   import cPickle as pickle
except:
   import pickle

postingsFileDir = "postings.txt" 
dictionaryFileDir = "dictionary.txt"
postingsFile = open(postingsFileDir, "rb")

DICTIONARY_POSTINGS = {}
DICTIONARY_FREQUENCY = {}
COLLECTION_N = 0

# Posting Pair Index
DOCID = 0
TF = 1

# Returns top k results
K_TOP = 10

# Debug Function to test single query
def testQuery(boolean_string):
   # Prepare dictionary
    global DICTIONARY_POSTINGS
    global DICTIONARY_FREQUENCY
    global DICTIONARY_LENGTH
    global COLLECTION_N

    dictionaryFile = open(dictionaryFileDir, "rb")
    dictionary = pickle.load(dictionaryFile)
    dictionaryFile.close()
    DICTIONARY_POSTINGS = dictionary["pointer"]
    DICTIONARY_FREQUENCY = dictionary["frequency"]
    DICTIONARY_LENGTH = dictionary["docLengthDict"]
    COLLECTION_N = dictionary["totalNumOfDocs"]

    outputFile = open("output.txt", "w")
    
    processQuery(boolean_string, outputFile)
    postingsFile.close()

# Main function to perform all queries in queryFile and output results to output file
def performQueries(queryFileDir, outputFileDir):
    # Prepare dictionary
    global DICTIONARY_POSTINGS
    global DICTIONARY_FREQUENCY
    global DICTIONARY_LENGTH
    global COLLECTION_N

    dictionaryFile = open(dictionaryFileDir, "rb")
    dictionary = pickle.load(dictionaryFile)
    dictionaryFile.close()
    DICTIONARY_POSTINGS = dictionary["pointer"]
    DICTIONARY_FREQUENCY = dictionary["frequency"]
    DICTIONARY_LENGTH = dictionary["docLengthDict"]
    COLLECTION_N = dictionary["totalNumOfDocs"]

    #Prepare outputFile
    outputFile = open(outputFileDir, "w")

    #Read queryFile
    queryFile = open(queryFileDir, "r")
    for line in queryFile:
        processQuery(line, outputFile)

    #Tear down when done
    tearDown(outputFile, queryFile)

def tearDown(outputFile, queryFile):
    postingsFile.close()
    outputFile.close()
    queryFile.close()

# Process query string
def processQuery(boolean_string, outputFile):

    # Stem query terms
    listOfTerms = word_tokenize(boolean_string)
    listOfTerms = refineTerms(listOfTerms)
    numberOfTerms = len(listOfTerms)
    #print(listOfTerms)

    dict_postingsPair = {} # Term : Array of postings pair (docID, tf)
    dict_doc_vector = {}
    dict_query_vector = {}
    query_vector = []
    docIDArray = []

    # Get all unique documents
    for term in listOfTerms:

        # Get array of postings pairs for this term
        postingsList = getPostingsList(term)

        # Save postings list into local dictionary
        dict_postingsPair[term] = postingsList

        # Append unique doc id
        docIDArray.extend(filter(lambda docId: docId not in docIDArray, 
                                            map(lambda pair: pair[DOCID], postingsList)))

    # Initialise dictionary of zero vectors with size = numberOfTerms
    for doc in docIDArray:
        dict_doc_vector[doc] = [0] * numberOfTerms

    # Initialise query vector
    query_vector = [0] * numberOfTerms

    # For each term in query
    for i in range(len(listOfTerms)):
        term = listOfTerms[i]
        # Construct query vector
        # Get tf
        termTfRaw = reduce(lambda x, y: x + (y == term), listOfTerms, 0)
        termTfWt = 1 + math.log10(termTfRaw)
        # Calculate idf
        docFreq = DICTIONARY_FREQUENCY.get(term)
        if docFreq > 0:
            idf = math.log10(COLLECTION_N / docFreq)
        else:
            idf = 0
        query_vector[i] = termTfWt * idf

        # For this term, get all documents and construct document vectors
        for postingsPair in dict_postingsPair[term]:

            # Calculate tfWt
            tfRaw = postingsPair[TF]
            if tfRaw > 0:
                tfWt = 1 + math.log10(tfRaw)
            else:
                tfWt = 0

            dict_doc_vector[postingsPair[DOCID]][i] = tfWt

    heap = []
    #print query_vector
    for doc in dict_doc_vector.keys():
        # Product of normalised document vector with query vector
        dict_doc_vector[doc] = vectorProduct(lengthNormaliseVector(dict_doc_vector[doc], doc), 
                                            query_vector)

        if len(heap) > K_TOP:
            heapq.heappushpop(heap, (getScore(dict_doc_vector[doc]), doc))
        else:
            heapq.heappush(heap, (getScore(dict_doc_vector[doc]), doc))
        #print doc, dict_doc_vector[doc]

    # Return Top K results
    topDoc = heapq.nlargest(K_TOP, heap)
    topDoc = map(lambda x: x[1], topDoc)
    #print topDoc
    writeResultsToOutputFile(topDoc, outputFile)

# Writes the input array of document ids to the outputFile in the correct format
# REQUIRE: outputFile has to be ready for writting beforehand
def writeResultsToOutputFile(results, outputFile):
    writtenString = ""

    if isEmpty(results):
        writtenString = ""
    else:
    # Loop through all terms append to writtenString with a space in between terms
        for term in results:
            writtenString += str(term) + " "

    # Remove trailing space
    writtenString = writtenString.strip()

    # Write to file
    outputFile.write(writtenString + "\n")

    # DEBUG print
    # print(writtenString)

# Convenience Methods
def isEmpty(list):
    return len(list) == 0

# Get the postings list for the given term
def getPostingsList(term):
    array = []
    # Get the index of the postings list byte position to load from. 
    # Default to -1 if not such term
    index = DICTIONARY_POSTINGS.get(term.lower(), -1)

    if index >= 0:
        postingsFile.seek(index)
        array = pickle.load(postingsFile)
    
    return array

# Vector Operations
def lengthNormaliseVector(vector, doc):
    length = DICTIONARY_LENGTH[doc]
    if length == 0:
        return map(lambda x: 0, vector);
    else:
        return map(lambda x: x / length, vector);

def magnitude(vector):
    return math.sqrt(sum(vector[i] * vector[i] for i in range(len(vector))))

def vectorProduct(vector1, vector2):
    for i in range(len(vector1)):
        vector1[i] = vector1[i] * vector2[i]
    return vector1

# Get the score of a vector (accumulate)
def getScore(vector):
    return reduce(lambda x, y: x + y, vector)

################## FOR REFINING QUERY TERMS ###################
def refineTerms(terms):
    stemmer = PorterStemmer()

    # Remove punctuations for OPERANDS (I THINK DONT NEED?)
    # terms = remove_punctuations(terms)

    # Combine Contracted Words for OPERANDS
    terms = combine_contracted(terms)

    # Stem OPERANDS
    terms = stem_tokens(terms, stemmer)

    # case-fold OPERANDS
    terms = case_fold(terms)

    return terms

def case_fold(tokens):
    caseFolded = []
    for token in tokens:
        caseFolded.append(token.lower())

    return caseFolded

# Stem tokens EXCEPT OPERATORS
def stem_tokens(tokens, stemmer):
    stemmed = []
    for token in tokens:
        stemmed.append(stemmer.stem(token))

    return stemmed

# Combines tokens for contracted words that were previously
# split due to word_tokenize, EXCLUDING OPERATORS
def combine_contracted(terms):
    
    # Returns input array if it does not have more than 2 elements
    if len(terms) < 2:
        return terms

    # Loop through all adjacnt word pairs
    refinedTerms = []
    for i in range(0, len(terms) - 1):
        j = i + 1
        firstWord = terms[i]
        secondWord = terms[j]

        # If second word contains aprostrophe (eg. 's), then combine
        # and assign to terms[i], leave terms[j] as empty string
        if "'" in secondWord:
            terms[i] = firstWord + secondWord
            terms[j] = ' '

    # Remove all entries with ' '
    for term in terms:
        if term != ' ':
            refinedTerms.append(term)

    return refinedTerms 

#####################################################

def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

#main program
dictionary_file_d = postings_file_p = query_file_q = output_file_o = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-d':
        dictionary_file_d = a
    elif o == '-p':
        postings_file_p = a
    elif o == '-q':
        query_file_q = a
    elif o == '-o':
        output_file_o = a
    else:
        assert False, "unhandled option"
if dictionary_file_d == None or postings_file_p == None or query_file_q == None or output_file_o == None:
    usage()
    sys.exit(2)

postingsFileDir = postings_file_p
dictionaryFileDir = dictionary_file_d
performQueries(query_file_q, output_file_o)

# testQuery("march acquisition")
