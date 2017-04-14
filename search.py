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
from datetime import datetime
try:
   import cPickle as pickle
except:
   import pickle

postingsFileDir = "postings.txt" 
dictionaryFileDir = "dictionary.txt"

DICTIONARY_POSTINGS = {}
DICTIONARY_DOCUMENTS = {}
COLLECTION_N = 0

# Posting Pair Index
DOCID = 0
POS = 1

# SGCA (court of appeal 1)
# SGDC (District Court 4)
# SGHC (high court 2)
# SGHCF (High court family 3)
# SGHC(I) (Singapore international commercial court 4)
# SGIAC (Industrial Arbitration Court 4)
# SGJC (youth court  4)
# SGMC (Magistrate's court 4)
# SGMCA (Military court of appeal 4)
# SGIPOS (Intellectual Property Office of Singapore 4)

# Court Ranking
courtScore = {
    "SGCA": 1,
    "SGHC": 0.75,
    "SGHCF": 0.75,
    "SGDC": 0.5,
    "SGMC": 0.5,
    "SGHC(I)": 0.5,
    "SGIAC": 0.5,
    "SGJC": 0.5,
    "SGMCA": 0.5,
    "SGIPOS": 0.5
}

# Debug Function to test single query
def testQuery(boolean_string):
   # Prepare dictionary
    global DICTIONARY_POSTINGS
    global DICTIONARY_DOCUMENTS
    global COLLECTION_N

    start = datetime.now()
    dictionaryFile = open(dictionaryFileDir, "rb")
    dictionary = pickle.load(dictionaryFile)
    dictionaryFile.close()
    DICTIONARY_POSTINGS = dictionary["pointer"]
    DICTIONARY_DOCUMENTS = dictionary["document"]
    COLLECTION_N = dictionary["collection"]

    outputFile = open("output.txt", "w")
    end = datetime.now()
    print "spin up took", (end - start).total_seconds()
    processQuery(boolean_string, outputFile)
    postingsFile.close()

# Main function to perform all queries in queryFile and output results to output file
def performQueries(queryFileDir, outputFileDir):
    # Prepare dictionary
    global DICTIONARY_POSTINGS
    global DICTIONARY_DOCUMENTS
    global COLLECTION_N

    start = datetime.now()
    dictionaryFile = open(dictionaryFileDir, "rb")
    dictionary = pickle.load(dictionaryFile)
    dictionaryFile.close()
    DICTIONARY_POSTINGS = dictionary["pointer"]
    DICTIONARY_DOCUMENTS = dictionary["document"]
    COLLECTION_N = dictionary["collection"]

    #Prepare outputFile
    outputFile = open(outputFileDir, "w")

    #Read queryFile
    queryFile = open(queryFileDir, "r")
    # Query on first line only
    line = queryFile.readline()
    end = datetime.now()
    print "spin up took", (end - start).total_seconds()
    processQuery(line, outputFile)

    #Tear down when done
    tearDown(outputFile, queryFile)

def tearDown(outputFile, queryFile):
    postingsFile.close()
    outputFile.close()
    queryFile.close()

# Process query string
def processQuery(boolean_string, outputFile):

    # Break down query into search terms
    searchTerms = getSearchTerms(boolean_string)
    tokens = []

    # --- Accumulate score ---
    numberOfTerms = len(searchTerms)
    docScoreDict = {}
    for phrase in searchTerms:
        start = datetime.now()
        print "iter:", phrase, "started"
        wordList = refineTerms(word_tokenize(phrase))
        for token in wordList:
            tokens.append(token)
        wordLen = len(wordList)
        # Accumulate cosine similarity score (+ phrasal match; + hard conjunction)
        docScoreDict = accumulateCosScore(wordList, docScoreDict)
        iteration = datetime.now()
        print "iteration:", phrase, "took", (iteration-start).total_seconds()

    # Accumulate score from modifiers, eg: matches Tag/Area of Law
    docScoreDict = accumulateExtraScore(tokens, docScoreDict)

    # Debug
    rank = []
    for doc in docScoreDict.keys():
        rank.append((doc, docScoreDict[doc]))

    rank.sort(key=lambda tup: tup[1], reverse = True)
    for item in rank:
        print item
    
    writeResultsToOutputFile(rank, outputFile)
  
# accumulate the score for each doc relevant to the phrase/wordList  
def accumulateCosScore(wordList, scoreDict):

    # --- Get phrasal match score --- :Rejected: Gives too many results
    # phrasalScore = getRelevantDocWithScore(wordList)
    # print "phrasal score:"
    # for doc in phrasalScore.keys():
    #     score = phrasalScore[doc]
    #     if score > 1:
    #         print doc, score

    # --- Get documents with exact phrasal match
    start = datetime.now()
    relevantDocs = getRelevantDocuments(wordList)
    end = datetime.now()
    print "phrasal match took:", (end-start).total_seconds()

    # --- Hard Conjunction --- :Used to further trim down results
    if not isEmpty(scoreDict.keys()):
        currentDocList = scoreDict.keys()
        intersectionAndRemoval = getIntersectionAndRemoval(sorted(currentDocList), 
                                                        relevantDocs)
        # remove non-intersecting documents from score dictionary
        if not isEmpty(intersectionAndRemoval[1]):
            for doc in intersectionAndRemoval[1]:
                scoreDict.pop(doc, None)

        # consider only the intersecting documents
        relevantDocs = intersectionAndRemoval[0]

    # --- Get TF-IDF score from Content ---
    numberOfWords = len(wordList)

    dict_postingsPair = {} # Term : Array of postings pair (docID, tf)
    dict_doc_vector = {}
    dict_query_vector = {}
    query_vector = []
    docIDArray = relevantDocs

    # Get all unique documents
    for word in wordList:

        # Get array of postings pairs for this term
        zoneWord = "content." + word
        postingsList = getPostingsList(zoneWord)

        # Save postings list into local dictionary
        filter(lambda p: p[DOCID] in docIDArray, postingsList)
        dict_postingsPair[word] = postingsList

        # Append unique doc id
        # docIDArray.extend(filter(lambda docId: docId not in docIDArray, 
        #                                     map(lambda pair: pair[DOCID], postingsList)))

    # Initialise dictionary of zero vectors with size = numberOfWords
    for doc in docIDArray:
        dict_doc_vector[doc] = [0] * numberOfWords

    # Initialise query vector
    query_vector = [0] * numberOfWords

    # For each term in query
    for i in range(numberOfWords):
        word = wordList[i]
        # Construct query vector
        # Assume tf = 1
        # termTfRaw = reduce(lambda x, y: x + (y == term), listOfTerms, 0)
        # termTfWt = 1 + math.log10(termTfRaw)
        # Calculate idf
        docFreq = len(dict_postingsPair[word])
        if docFreq > 0:
            idf = math.log10(COLLECTION_N / docFreq)
        else:
            idf = 0
        query_vector[i] = idf

        # For this term, get all documents and construct document vectors
        for postingsPair in dict_postingsPair[word]:
            if postingsPair[DOCID] in dict_doc_vector:
                # Calculate tfWt
                tfRaw = len(postingsPair[POS])
                if tfRaw > 0:
                    tfWt = 1 + math.log10(tfRaw)
                else:
                    tfWt = 0

                dict_doc_vector[postingsPair[DOCID]][i] = tfWt

    # Calculate cos product score
    cosProdScore = {}
    for doc in dict_doc_vector.keys():
        # Product of normalised document vector with query vector
        docLength = DICTIONARY_DOCUMENTS[doc]["contentlength"]
        query_vector = normaliseVector(query_vector)
        dict_doc_vector[doc] = vectorProduct(lengthNormaliseVector(dict_doc_vector[doc], docLength), 
                                            query_vector)
        cosProdScore[doc] = magnitude(dict_doc_vector[doc])

    # Tabulate intermediate score :Rejected: Not using partial phrasal match
    # for doc in phrasalScore.keys():
    #     intScore = phrasalScore[doc]
    #     if intScore < 2:
    #         intScore = 0 # Debug: Consider phrasal matches of at least 2 words
    #     intScore *= cosProdScore.get(doc, 0)
    #     # accumulate scoreDict
    #     accScore = scoreDict.get(doc, 0)
    #     accScore += intScore
    #     if accScore > 0:
    #         scoreDict[doc] = accScore

    # Add cosScore
    for doc in docIDArray:
        cosScore = cosProdScore.get(doc, 0)
        accScore = scoreDict.get(doc, 0)
        accScore += cosScore
        if accScore > 0:
            scoreDict[doc] = accScore

    # Return accumulated scores
    return scoreDict

# Accumulate score from other aspects, Eg: matching Tags/ Area of Law
def accumulateExtraScore(tokens, scoreDict):
    # --- Modifiers ---
    mod_source = 0.1
    mod_content = 0.1
    mod_court = 0.2
    mod_tag = 0.3
    mod_law = 0.3

    # Accumulate extra score for each document in dictionary
    for doc in scoreDict.keys():
        docMetaData = DICTIONARY_DOCUMENTS[doc]
        extraScore = 0
        # Process sourceType [str]
        sourceType = docMetaData.get("source_type", "nil")
        if sourceType != "nil":
            if sourceType == "primary":
                extraScore += mod_source

        # Process content_type [str]
        contentType = docMetaData.get("content_type", "nil")
        if contentType != "nil":
            if contentType == "case":
                extraScore += mod_content

        # Process court [str]
        court = docMetaData.get("court", "nil")
        if court != "nil":
            score = courtScore.get(court, 0)
            extraScore += mod_court * score

        # process tag [arr]
        tags = docMetaData.get("tag", [])
        numMatches = 0
        if not isEmpty(tags):
            
            # Go through every token, check for a match with the tagsCopied array
            for token in tokens:
                for tag in tags:

                    # If matched, remove this tag from tagsCopied so that this match will not happen again
                    if token in tag:
                        numMatches += 1

            # count how many tags were removed / total tags --> Proportion to the mod_tag score
            extraScore += (1.0 * numMatches / len(tags)) * mod_tag

        # process areaoflaw [arr]
        areaoflaw = docMetaData.get("areaoflaw", [])
        numMatches = 0
        if not isEmpty(areaoflaw):
            
            # Go through every token, check for a match with the areasCopied array
            for token in tokens:
                for area in areaoflaw:

                    # If matched, remove this area from areasCopied so that this match will not happen again
                    if token in area:
                        numMatches += 1

            # count how many elements were removed / total elements --> Proportion to the mod_law score
            extraScore += (1.0 * numMatches / len(areaoflaw)) * mod_law

        # Update score, add multiplier to score
        if extraScore > 0:
            scoreDict[doc] += (scoreDict[doc] * extraScore)

    return scoreDict

# Writes the input array of document ids to the outputFile in the correct format
# REQUIRE: outputFile has to be ready for writting beforehand
def writeResultsToOutputFile(rank, outputFile):
    writtenString = ""

    if isEmpty(rank):
        writtenString = ""
    else:
    # Loop through all terms append to writtenString with a space in between terms
        for item in rank:
            writtenString += str(item[0]) + " "

    # Remove trailing space
    writtenString = writtenString.strip()

    # Write to file
    outputFile.write(writtenString)

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

# Used for retrieving documents that has an exact match of the given wordList.
def getRelevantDocuments(wordList):
    # wordList = refineTerms(word_tokenize(searchTerms))
    wordLen = len(wordList)

    # Get postings lists for all words
    postingsLists = []
    for word in wordList:
        word = "content." + word
        postingsLists.append(getPostingsList(word))

    initialList = postingsLists[0]
    # If phrase has only 1 word, return the postings list
    if wordLen == 1:
        relevantDocs = map(lambda pair: pair[DOCID], initialList)
        return relevantDocs

    # Filter out docs that are found in all words' postings list in phrase
    for listIndex in range(1, wordLen):
        relevant = []
        nextList = postingsLists[listIndex]
        c1 = 0
        c2 = 0
        while c1 < len(initialList) and c2 < len(nextList):
            if initialList[c1][0] == nextList[c2][0]:
                relevant.append(initialList[c1][0])
                c1 += 1
                c2 += 1
            else:
                if initialList[c1][0] > nextList[c2][0]:
                    c2 += 1
                else:
                    c1 += 1

        initialList = filter(lambda p: p[0] in relevant, initialList)

    relevantDocIds = map(lambda p: p[0], initialList)
    postingsLists = map(lambda list: filter(lambda p: p[0] in relevantDocIds, list), postingsLists)

    relevantDocs = []
    nextDoc = 0 # Switch to jump to next doc
    # using the first list as ref (as it has the first word)
    for pairIndex in range(len(postingsLists[0])):
        # For each pair, for each position in pair, check if subsequent positions exist in subsequent lists/words
        pair = postingsLists[0][pairIndex]
        for pos in pair[1]:
            if nextDoc:
                nextDoc = 0
                break
            for listIndex in range(1, wordLen):
                # Check if subsequent list contain next position
                currentList = postingsLists[listIndex]
                if (pos + listIndex) in currentList[pairIndex][1]:
                    # Check if is last word/list
                    if (listIndex == wordLen - 1):
                        relevantDocs.append(currentList[pairIndex][0])
                        # Break to next doc
                        nextDoc = 1
                        break
                    # Else proceed to check for next word/list
                    else:
                        continue
                # If not, break to next starting pos in initial pair
                else:
                    break

    return relevantDocs

# Used for retrieving documents that satisfy partial matches and append a score to their degree of match
def getRelevantDocWithScore(wordList):

    # Helper function to filter out partial matches that falls below a threshold value
    def checkPairScore(pair, currentListIndex):
        docId = pair[0]
        positions = pair[1]
        offset = 0
        score = 1
        for nextListIndex in range(currentListIndex + 1, len(postingsLists)):
            offset += 1
            nextList = postingsLists[nextListIndex]
            similarDocPair = filter(lambda p: p[0] == docId, nextList)
            if len(similarDocPair) > 0:
                for pos in positions:
                    if (pos + offset) in similarDocPair[0][1]:
                        score += 1
                        break
        return score

    # wordList = refineTerms(word_tokenize(searchTerms))
    wordLen = len(wordList)

    # Get postings lists for all words
    postingsLists = []
    for word in wordList:
        word = "content." + word
        postingsLists.append(getPostingsList(word))

    result = {}
    for plIndex in range(len(postingsLists)):
        pl = postingsLists[plIndex]
        for pair in pl:
            score = checkPairScore(pair, plIndex)
            oldScore = result.get(pair[0], 0)
            if oldScore < score:
                result.update({pair[0]: score})

    # Dictionary of (docID: score)
    return result

def getIntersectionAndRemoval(list1, list2):
    # Returns a Pair containing:
    # 1. the list of elements that intersect both lists
    # 2. the list of elements in list1 which do not intersect
    # Assumes list1 and list2 are sorted
    intersection = []
    removal = []
    c1 = 0
    c2 = 0
    # Do a linear traversal of both lists
    while c1 < len(list1) and c2 < len(list2):
        if list1[c1] == list2[c2]:
            intersection.append(list1[c1])
            c1 += 1
            c2 += 1
        elif list1[c1] > list2[c2]:
            c2 += 1
        else:
            removal.append(list1[c1])
            c1 += 1

    # If there are remaining entries in list1, append them to removal
    while c1 < len(list1):
        removal.append(list1[c1])
        c1 += 1

    return (intersection, removal)

# Vector Operations
def normaliseVector(vector):
    lengthSq = 0
    for i in range(len(vector)):
        lengthSq += math.pow(vector[i], 2)

    length = math.sqrt(lengthSq)
    return map(lambda x: x / length, vector)

def lengthNormaliseVector(vector, length):
    if length == 0:
        return map(lambda x: 0, vector)
    else:
        return map(lambda x: x / length, vector)

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

def getSearchTerms(query):
    searchTerms = query.split('AND')
    searchTerms = map(lambda t: t.split('"')[1], searchTerms)
    return searchTerms

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
postingsFile = open(postingsFileDir, "rb")
performQueries(query_file_q, output_file_o)

#testQuery('''"intentional tort" AND "remoteness of damage"''')
