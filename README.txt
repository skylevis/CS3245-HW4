This is the README file for A0124552M-A0131003J submission
Emails: A0124552@u.nus.edu ; A0131003@u.nus.edu

== Python Version ==

We're using Python Version 2.7.x for this assignment.

== General Notes about this assignment ==

// INDEX PHASE //

For indexing, the preprocessing done is mostly similar to the indexing used in HW2, where we first remove all punctuations (except hyphens and aprostophes), manually concat back all tokenized contraction words, separate words that come before and after a forward slash, and do casefolding + stemming.   

We also included information for the total number of documents in the entire collection and the document raw length in our dictionary.txt file. 

// SEARCH PHASE //

For the document score calculation (lnc), we followed as per the instructions and used the raw document length to do normalisation of the document score vectors, instead of that on the w7 slides "auto best car insurance" example - where we identify the total number of unique terms in each document (this would be the number of dimensions for each of the vector) and do normalisation in the Euclidean way. 

We noticed that the length normalisation had a huge impact on the original scores.

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

