This is the README file for A0124552M-A0131003J submission
Emails: A0124552@u.nus.edu ; A0131003@u.nus.edu

== Python Version ==

We're using Python Version 2.7.x for this assignment.

== General Notes about this assignment ==

// *** OVERVIEW *** //

The general structure consists of the Indexer (as done in index.py), the XmlParser (in xmlparser.py) and the Search component which is in charge of executing the queries (in search.py) 

Similiar to HW2 and HW3, the indexer will index the corpus and writes the dictionary and postings list into separate files, which will then be accessed by the searching script.

// *** INDEX *** //

== XML PARSING ==

To parse the documents in the intellex directory, we have to use a XML parser. After looking through the built-in xml parsers availabe to python readily, we decided to make use of the xml.dom library's light weight minidom parser. We decided to provide support for extracting as much information as possible from the document and worry about their usage later. To simplify the xml parsing subsequently in the indexer, we also encapsulated the parsing functionality into a XMLParser object.

== ZONAL INDEXING ==

To ensure that the search.py algorithm works correctly, we also attempted to stem the data in the zones similar to how we did for indexing the data in the content. This is to ensure that subsequent matching in the search algorithm can be generalised for both content and other zones, reducing the chances for error.

== POSITIONAL INDICES ==

To accommodate phrasal queries, we made use of positional indices. Basically, every posting is now a tuple containing the document ID that the word is found in, and a positional array containing the positions of the word in the document. The length of the array is now the term frequency for this term. 

== OPTIMISING STEMMING ==

We realised that for our program, indexing takes too long (way past 20 mins for just the Singapore's corpus). We tracked down the bottleneck for indexing each document, and discovered that stemming was the main culprit for slowing the indexing process. Because we have no control over the way the library carries out stemming, we decided to do caching on our side so as to speed up the stemming process. For every new word encountered, we store the original word as the key and its stemmed counterpart as the value in a locally defined dictionary. From there, before we attempt to stem a word, the program will try to find a word that is already stemmed beforehand first before actually using the library's stem function. This sped up the indexing process by 4 times, allowing us to index the Singapore's corpus in about 10 mins.

// *** SEARCH PHASE *** //

== PHRASAL MATCH ==

First, we will cut down the number of possible document matches by removing documents that do not contain the phrase(s) in the query. This is done by first retrieving the positional index of the 1st word in the phrase, and then checking the posting list for the next word in the phrase to see if its posiitonal index comes right after the previous one.  

Before we settled on hard conjunction of phrasal match, we tried out a partial phrasal match algorithm, which means that we do not eliminate the document if only a part of the given phrase is found in the document. However, we realised that this has resulted in way too many documents (too many to be considered relevant at all), and thus switched back to hard conjunction. 

== HARD CONJUNCTION ==

Next, we will further reduce the number of possible document matches by removing documents that do not contain all the phrases in the query. We do this using the "hard conjunction" way, in which as long as a document does not contain any one of the phrases, it will be removed. Initially, we tried to do the soft conjunction method /********************** TODO : INSERT EXPLAINATION HERE

== TF-IDF CALCULATION ==

With a reduced amount of total documents now, we can then calculate the TF-IDF score without compensating that much performance. 
Similar to HW3, we used the LNC.LTC way to calculate the TF-IDF scores for each document. The only difference is that in our HW3, we made a mistake by normalising the score using the document's raw length (number of words). In this assignment, we corrected to using the number of UNIQUE words in the document. This is already precalculated and stored during the indexing phase, so we can easily access it during search runtime. 

== FIELD/ZONAL SCORES ==

Lastly, we take into account of the zonal scores by setting our own score modifiers for each zonal element. These scores are tweaked and adjusted through trial and error. We also make sure that zones like "tags" and "area of law" which are more critical for relevance are therefore given a higher weightage compared to other zones. To prevent documents which exploits a large (raw) number of tags and areas of law, we normalise the scores according to the total number of occurences in the document. The final zonal score is then multipled to the TD-IDF score of the document as caluclated previously.

== Work allocation ==

While most of the assignment we discussed and implemented together, a general work breakdown is as follow:
A0131003J implemented the positional indexing, TF-IDF calculation and field/zonal scores calculation
A0124552M implemented the XML parsing, optimising, phrasal matching and other i/o related things. 


== Files included with this submission ==

dictionary.txt --> This file contains the byte version of the dictionaries produced from index phase.
index.py --> The code for the indexing phase
search.py --> Code for the searching phase and boolean query processing
postings.txt --> This file contains the byte version of all the postings lists produced from index phase

== Statement of individual work ==

Please initial one of the following statements.

[X] We, A0124552M-A0131003J, certify that I have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, I
expressly vow that I have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] We, A0124552M-A0131003J, did not follow the class rules regarding homework
assignment, because of the following reason:

<Please fill in>

I suggest that I should be graded as follows:

<Please fill in>

== References ==

