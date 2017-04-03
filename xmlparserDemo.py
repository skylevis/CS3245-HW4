from xmlparser import XMLParser
import math

# xmlparser = XMLParser()
# xmlparser.parseDoc("intellex/2021482.xml")
# print xmlparser.date

# string = '''"intentional tort" AND "remoteness of damage"'''
# f = open("queries/q2.txt")
# string = f.readline()
# searchTerms = string.split('AND')
# searchTerms = map(lambda t: t.split('"')[1], searchTerms)

# print searchTerms

# def checkPairScore(pair, currentListIndex):
# 	docId = pair[0]
# 	positions = pair[1]
# 	offset = 0
# 	score = 1
# 	for nextListIndex in range(currentListIndex + 1, len(postingsLists)):
# 		offset += 1
# 		nextList = postingsLists[nextListIndex]
# 		similarDocPair = filter(lambda p: p[0] == docId, nextList)
# 		if len(similarDocPair) > 0:
# 			for pos in positions:
# 				if (pos + offset) in similarDocPair[0][1]:
# 					score += 1
# 					break
# 	return score

# sampleDict = {
# 			"word1": [(1, [2, 4, 5]), (3, [3, 6, 10]), (4, [1]), (6, [9])],
# 			"word2": [(1, [5, 10]), (3, [4, 7]), (6, [10])],
# 			"word3": [(3, [5]), (4, [2]), (6, [11])],
# 			"word4": [(3, [6, 10]), (10, [100])]
# 			}

# wordList = ["word1", "word2", "word3", "word4"]
# wordLen = len(wordList)

# # Get postings lists for all words
# postingsLists = []
# for word in wordList:
# 	postingsLists.append(sampleDict[word])

# result = {}
# for plIndex in range(len(postingsLists)):
# 	pl = postingsLists[plIndex]
# 	for pair in pl:
# 		score = checkPairScore(pair, plIndex)
# 		oldScore = result.get(pair[0], 0)
# 		if oldScore < score:
# 			result.update({pair[0]: score})

# print result

# for each list, starting from list 0
# for each pair in list
# check if doc Id exist in subsequent lists
	# if so, check if trailing position exist in subsequent list
		# if so, add score
		# else, check next position in initial pair
	# 




# # Filter out docs that are found in all lists
# initialList = postingsLists[0]
# for listIndex in range(1, wordLen):
# 	relevant = []
# 	nextList = postingsLists[listIndex]
# 	c1 = 0
# 	c2 = 0
# 	while c1 < len(initialList) and c2 < len(nextList):
# 		if initialList[c1][0] == nextList[c2][0]:
# 			relevant.append(initialList[c1][0])
# 			c1 += 1
# 			c2 += 1
# 		else:
# 			if initialList[c1][0] > nextList[c2][0]:
# 				c2 += 1
# 			else:
# 				c1 += 1

# 	initialList = filter(lambda p: p[0] in relevant, initialList)

# relevantDocIds = map(lambda p: p[0], initialList)
# postingsLists = map(lambda list: filter(lambda p: p[0] in relevantDocIds, list), postingsLists)
# #print(postingsLists)

# result = []
# # using the first list as ref (as it has the first word)
# for pairIndex in range(len(postingsLists[0])):
# 	pair = postingsLists[0][pairIndex]
# 	for pos in pair[1]:
# 		for listIndex in range(1, wordLen):
# 			currentList = postingsLists[listIndex]
# 			if (pos + listIndex) in currentList[pairIndex][1]:
# 				if (listIndex == wordLen - 1):
# 					result.append(currentList[pairIndex][0])
# 				else:
# 					continue
# 			else:
# 				break

# print result

a = [4]
a.append(4)
print a