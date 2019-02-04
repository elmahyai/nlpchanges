import json
import os
import datetime
import math
from collections import Counter
import nltk
#dler = nltk.downloader.Downloader()
#dler._update_index()
#dler._status_cache['panlex_lite'] = 'installed' # Trick the index to treat panlex_lite as it's already installed.
#dler.download('popular')
## nltk.download()   ## ensure nltk is installed properly

nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')

from nltk.tokenize import word_tokenize
import re
from nltk.tag import StanfordNERTagger
from nltk.corpus import stopwords
stop = set(stopwords.words('english'))
import sqlite3 as lite
import pandas as pd



def generate_json ( prepareFilesAdress, prepareFilesAllForm4):
    wordsList = list()
    try :
        txtFiles = os.listdir(path=prepareFilesAdress)
    except:
        print('check  prepareFilesAdress in the config file' )
    
    for i in range(len(txtFiles)):
        filePath = prepareFilesAdress+'/'+txtFiles[i]
        if checkForm4(filePath, prepareFilesAllForm4) == True:
            with open(filePath, 'r') as f:
                t = f.read()
                t2 = re.sub('[^a-zA-Z]+', '', t)
                t2 = nltk.word_tokenize(t)
                t3 = list(set(t2))
                t4 = [t for t in t3 if t.isalpha()]
                # change camelCase to normal words
                t5 = [re.sub("([a-z])([A-Z])","\g<1> \g<2>",label).split(' ') for label in t4]
                flat_list = [item for sublist in t5 for item in sublist]
                t5 = [re.sub("([a-z])([A-Z])([A-Z])","\g<1> \g<2> \g<2>",label).split(' ') for label in flat_list]
                flat_list = [item for sublist in t5 for item in sublist]
                words = list(set(flat_list))
                wordsList.append(words)
                print(len(wordsList))
    words = [item for sublist in wordsList for item in sublist]
    words = [w for w in words if not w.isupper() and not w.isnumeric() and w not in stop and len(w)> 3]
    words2 = list(set(words))
    with open('changeWords.json','w') as f:
        json.dump(words2, f)          
            
        
def checkForm4(filePath, prepareFilesAllForm4):
    if prepareFilesAllForm4 == "True":
        return True
    f = open(filePath, "r") 
    x = 0
    for line in f:
        x = x + 1
        if re.match(r'CONFORMED SUBMISSION TYPE.*4', line):
            print('Form 4 found')
            return(True)
        elif x == 10:
            return(False)

    f.close()
        
#not_number
#checks if the word is not a number

def not_number(s):
    try:
        s = s.replace(',','')
        float(s)
        return False
    except ValueError:
        return True
    
# counter_cosine_similarity, length_similarity, similarity_score
# functions to calculate similarity between two lists


def counter_cosine_similarity(c1, c2):
    terms = set(c1).union(c2)
    dotprod = sum(c1.get(k, 0) * c2.get(k, 0) for k in terms)
    magA = math.sqrt(sum(c1.get(k, 0)**2 for k in terms))
    magB = math.sqrt(sum(c2.get(k, 0)**2 for k in terms))
    return dotprod / (magA * magB)

def length_similarity(c1, c2):
    lenc1 = sum(c1.values())
    lenc2 = sum(c2.values())
    return min(lenc1, lenc2) / float(max(lenc1, lenc2))

def similarity_score(l1, l2):
    c1, c2 = Counter(l1), Counter(l2)
    return length_similarity(c1, c2) * counter_cosine_similarity(c1, c2)



#Extracting identity names¶
#given the tokens: words in the text it runs the stanford tagger to find names and
# then returns name + some features e.g. 40 words around it, the location of the sentence ,etc.
def extractNames(tokens, date, fileName, ner_tagger):
    tags = ner_tagger.tag(tokens)
    i = 0
    extractedNames = []
    number_of_words = len(tags)
    while i < number_of_words:
        x,y = tags[i]
        if y != 'O':
            name = x
            oldy = y
            location = i # relative to the length of the text
            try:
                words_before_name = [x for x,y in tags[(i-10):(i-1)]]
                
            # except if word in the start of text
            except:
                words_before_name = []
                print("exception happend")

            try:
                words_after_name = [x for x,y in tags[(i+1):(i + 30)]]
            
            except: 
                words_after_name = []
                print("exception happend")

            
            
            # looping again to collapse names that consists of two or more words
            while True:
                i = i + 1
                x,y = tags[i]
                if y != 'O':
                    name = name + ' ' + x
                else: 
                    break;
                    
                    
            words_around = words_before_name + words_after_name
            number_of_stop_words_around = len([word for word in words_around if word in stop])
            number_of_numbers_around = len([word for word in words_around if not_number(word)])
            number_of_symbols_around = len([word for word in words_around if len(word)<2])
            words_around = [word.lower() for word in words_around if ((word not in stop) and  (not_number(word)) and (len(word) > 1) and word.isalpha())]
            words_around = [t for t in words_around]
            
            extractedNames.append((name,oldy, location, words_around, number_of_stop_words_around,
                                  number_of_numbers_around, number_of_symbols_around, date, fileName))
        else:
            i = i + 1
    
    
    return(extractedNames)


#extractDate
#returns the date of the file
 
def extractDate(filePath):
    f = open(filePath, "r") 
    x = 0
    date = datetime.datetime(1000, 1, 1)
    for line in f:
        x = x + 1
        # modify this to the line containing the date 
        # possible scrape dates but for now it seeems all files has a date specified in the beginning of file 
        r = re.match(r'FILED AS OF DATE.*', line)
        if r:
            r = re.search('[0-9].*',r.group()).group()
            date = datetime.datetime(int(r[0:4]), int(r[4:6]), int(r[6:8]))
            break;
        elif x == 100:
            break;
    
    return(date)
    f.close()
    
#   extractFile
#given a filePath it runs previous functions and returns a list of names each item
# is a set of (name, location, important words mentioned, sentence, etc) 
    
def extractFile (filePath, ner_tagger):
    f = open(filePath,'r')
    txt = f.read()
    f.close()
    date = extractDate(filePath)
    tokens = word_tokenize(txt)
    fileName = filePath.split('/')[-1]
    names = extractNames(tokens, date, fileName, ner_tagger)
    return(names)
    
#    extract_useful_information_from_t
#Since t could include more information than needed for the current purpose, we subset t to newt : here I choose
# only names of persons and only persons who are surrounds by 8 or more important words.


def extract_useful_information_from_t(t, tokens,  importantWords, whoToScrape = "PERSON"):
    newt = list()
    for a,b,location,d,e,f,g,date,fileName in t:
        i = 0
        foundwords = []
        for item in d:
            if item in importantWords:
                foundwords.append(item)
                i = i + 1
        if b == whoToScrape:
            if i > 7 :
                newt.append((a, ','.join(set(foundwords)), ' '.join(tokens[(location-10):(location + 20)]),
                             date, fileName, location))

    return(newt)


#modify_database¶
#given newt list of names and a connection to our database it: first checks
# if the names is appearing for the first time then if the names appeared before, it checks if the important words around it are < 50 % similar to the important words around the name in 
#the current text, if so, we conside the information new and add it to the database.

def modify_person_database(newt, con, dublicationLimit):
    cur = con.cursor()
    for tt in newt:
        name = tt[0]
        importantWords = tt[1].split(',')

        cur.execute("SELECT id, importantWords FROM personChanges WHERE name=?", (name,))

        c = cur.fetchall()
        if len(c) == 0:
            print("First appearance of the entity name")
            duplicationProbability  = 0
            tt = tt + (duplicationProbability,)
            #print(tt[2])
            cur.execute("""INSERT INTO personChanges (name , importantWords, sentence , date , 
                                                    fileName, locationOfNameByWord,
                                                    duplicationProbability) VALUES(?,?,?,?,?,?,?) """,tt )
            continue;
        s = list()
        for iD, impWords in c:
            l = impWords.split(',')
            ss = similarity_score(l, importantWords)
            s.append(ss)
        duplicationProbability = max(s)
        if duplicationProbability < dublicationLimit:
            # If information is new
            print("Found new changes!")
            tt = tt + (duplicationProbability,)
            #print(tt[2])
            cur.execute("""INSERT INTO personChanges (name , importantWords, sentence , date,
                                                      fileName, locationOfNameByWord,
                                                      duplicationProbability) VALUES(?,?,?,?,?,?,?) """,tt )
        else:
            # old information
            print("old info already stored in Database")
            tt = tt + (iD,duplicationProbability,)
            cur.execute("""INSERT INTO dublicatesLogPerson (name , importantWords, sentence , date,
                                                      fileName, locationOfNameByWord, 
                                                      dublicatedID, duplicationProbability) 
                VALUES(?,?,?,?,?,?,?,?) """,tt )

    con.commit()




def modify_organization_database(newt, con, dublicationLimit):
    cur = con.cursor()
    for tt in newt:
        name = tt[0]
        importantWords = tt[1].split(',')

        cur.execute("SELECT id, importantWords FROM organizationChanges WHERE name=?", (name,))

        c = cur.fetchall()
        if len(c) == 0:
            print("First appearance of the entity name")
            #print(tt[2])
            duplicationProbability  = 0
            tt = tt + (duplicationProbability,)
            cur.execute("""INSERT INTO organizationChanges (name , importantWords, sentence , date , 
                                                    fileName, locationOfNameByWord,
                                                    duplicationProbability) VALUES(?,?,?,?,?,?,?) """,tt )
            continue;
        s = list()
        for iD, impWords in c:
            l = impWords.split(',')
            ss = similarity_score(l, importantWords)
            s.append(ss)
        duplicationProbability = max(s)
        if duplicationProbability < dublicationLimit:
            # If information is new
            print("Found new changes!")
            tt = tt + (duplicationProbability,)
            #print(tt[2])
            cur.execute("""INSERT INTO organizationChanges (name , importantWords, sentence , date,
                                                      fileName, locationOfNameByWord,
                                                      duplicationProbability) VALUES(?,?,?,?,?,?,?) """,tt )
        else:
            # old information
            print("old info already stored in Database")
            tt = tt + (iD,duplicationProbability,)
            cur.execute("""INSERT INTO dublicatesLogOrganization (name , importantWords, sentence , date,
                                                      fileName, locationOfNameByWord,
                                                      dublicatedID, duplicationProbability) 
                VALUES(?,?,?,?,?,?,?,?) """,tt )

    con.commit()














def generate_nlp_process( targetFiles,targetFilesAdress, importantWords , entityClassifierAddress, englishModelAddress,
                         scrapePerson , scrapeOrganization, con, dublicationLimit ):
    ner_tagger = StanfordNERTagger(englishModelAddress, entityClassifierAddress)
    # encoding='utf8' 
    for i in range(len(targetFiles)):
        try:
            if targetFilesAdress.endswith('/'):
                filePath = targetFilesAdress + targetFiles[i]    
            else:
                filePath = targetFilesAdress + '/' + targetFiles[i]
                
            f = open(filePath,'r')
            txt = f.read()
            tokens = word_tokenize(txt)
            f.close()
            t = extractFile(filePath, ner_tagger)
            if scrapePerson == "True":
                newt = extract_useful_information_from_t(t, tokens,  importantWords, whoToScrape = "PERSON")
                modify_person_database(newt, con, dublicationLimit)
            if scrapeOrganization == "True":
                newt = extract_useful_information_from_t(t,  tokens,  importantWords, whoToScrape = "ORGANIZATION")
                modify_organization_database(newt, con, dublicationLimit)
        except:
            print("Error occurred while scraping file"+ filePath + "....Moving to the next file")
    
class changesNotifier:
    def __init__(self, configFilePath ):        
        with open(configFilePath) as f:
            config = json.load(f)
        
        self.entityClassifierAddress = config['entityClassifierAddress']
        self.englishModelAddress = config['englishModelAddress']
        self.prepareFilesAdress = config['prepareFilesAdress']
        self.prepareFilesAllForm4 = config['prepareFilesAllForm4']
        self.targetFilesAdress = config['targetFilesAdress']
        self.usePreexistingPreparedWordlist = config['usePreexistingPreparedWordlist']
        self.wordListAddress = config['wordListAddress']
        self.databaseAddress = config['databaseAddress']
        
        self.scrapePerson = config['scrapePerson']
        self.scrapeOrganization = config['scrapeOrganizatio']
        self.dublicationLimit = float(config['dublicationLimit'])
        #Important words¶
        #these are words mentioned in form 4 after some editing. I created it in a
        # separate code. you should have changeWords.json in the same folder of this 
        #script. Improving it will significantly improve the detection accuracy
        if self.usePreexistingPreparedWordlist == 'True':
            with open(self.wordListAddress,'r') as f:
                self.importantWords = json.load(f)
        else :
            generate_json ( prepareFilesAdress =  self.prepareFilesAdress, 
                   prepareFilesAllForm4 = self.prepareFilesAllForm4)
            with open(self.wordListAddress,'r') as f:
                self.importantWords = json.load(f)
        
        
        #loading text files
        #Now we load all files in data folder and loop through them, here I will loop through first ten
        
        self.targetFiles = os.listdir(path=self.targetFilesAdress)
        
        
        
        self.con = lite.connect(self.databaseAddress)
        
        

        # Create a database to store data in a table called changes with the following columns:
        #name : entity name importantWords : important words that appear around the entity
        # names sentence : the sentence the entity name is mentioned in date :
        #    the date of the document the entity name was mentioned in


        with self.con:
            cur = self.con.cursor()
            cur.execute("""CREATE TABLE  IF NOT EXISTS personChanges(
                    id INTEGER PRIMARY KEY, name TEXT, importantWords TEXT , 
                    sentence TEXT, date DATETIME, fileName TEXT, locationOfNameByWord integer,
                    duplicationProbability REAL)""")
            
            cur.execute("""CREATE TABLE  IF NOT EXISTS organizationChanges(
                    id INTEGER PRIMARY KEY, name TEXT, importantWords TEXT , 
                    sentence TEXT, date DATETIME, fileName TEXT, locationOfNameByWord integer,
                    duplicationProbability REAL)""")
            
            cur.execute("""CREATE TABLE  IF NOT EXISTS dublicatesLogPerson(
                    id integer PRIMARY KEY, name TEXT, importantWords TEXT , 
                    sentence TEXT, date DATETIME, fileName TEXT, locationOfNameByWord integer, 
                    dublicatedID INTEGER, duplicationProbability REAL)""")
            
            cur.execute("""CREATE TABLE  IF NOT EXISTS dublicatesLogOrganization(
                    id integer PRIMARY KEY, name TEXT, importantWords TEXT , 
                    sentence TEXT, date DATETIME, fileName TEXT, locationOfNameByWord integer, 
                    dublicatedID INTEGER, duplicationProbability REAL)""")
    
    def runModel(self):
        
        generate_nlp_process( self.targetFiles,self.targetFilesAdress, self.importantWords , self.entityClassifierAddress,
                             self.englishModelAddress, self.scrapePerson , self.scrapeOrganization, self.con ,
                             self.dublicationLimit)

    def generateImportantWords(self):
        generate_json ( prepareFilesAdress =  self.prepareFilesAdress, 
                   prepareFilesAllForm4 = self.prepareFilesAllForm4)







class databaseManager():
    def __init__(self, configFilePath):
        with open(configFilePath) as f:
            config = json.load(f)
        self.databaseAddress = config['databaseAddress']
        self.con = lite.connect(self.databaseAddress)


    def searchPerson(self, name, wordInSentence='', minimumdublicationProbability= 0,
                     start_date = '1800-01-01', end_date = '3000-01-01'):
        print("Make sure date is in this format 1800-01-21")
        # document type : easy to add similar to date we have to modify code to specify the 
        # sentence before date and document type.
        with self.con:
            # cur = self.con.cursor()
            query = """
                SELECT * FROM personChanges WHERE (
                (name LIKE '%s') AND
                date BETWEEN date('%s') AND date('%s') AND 
                (sentence LIKE '%s') AND
                (duplicationProbability >=%f)
                )
                """ % ('%' + name + '%', start_date, end_date, '%' + wordInSentence  + '%',
                    minimumdublicationProbability)
            
            df = pd.read_sql(query, self.con)
            
            
            
            print("\n.............saved query to saved.csv")
            df.to_csv("saved.csv", sep='\t')

            return(df)
           


    def searchOrganization(self, name, wordInSentence='', minimumdublicationProbability= 0,
                         start_date = '1800-01-01', end_date = '3000-01-01'):
            print("Make sure date is in this format 1800-01-21")
            # document type : easy to add similar to date we have to modify code to specify the 
            # sentence before date and document type.
            with self.con:
                # cur = self.con.cursor()
                query = """
                    SELECT * FROM organizationChanges WHERE (
                    (name LIKE '%s') AND
                    date BETWEEN date('%s') AND date('%s') AND 
                    (sentence LIKE '%s') AND
                    (duplicationProbability >=%f)
                    )
                    """ % ('%' + name + '%', start_date, end_date, '%' + wordInSentence  + '%',
                        minimumdublicationProbability)
                
                df = pd.read_sql(query, self.con)
                
                
                
                print("\n.............saved query to saved.csv")
                df.to_csv("saved.csv", sep='\t')
    
                return(df)
                
            
if __name__ == "__main__":
    FTR = changesNotifier("config.json")

    FTR.runModel()
#    FTR.generateImportantWords()

                