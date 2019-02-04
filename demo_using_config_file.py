# config file should be edited to the correct adress of the files 

from changesNotifier import *
FTR = changesNotifier("config.json")


dbman = databaseManager("config.json")


# 
FTR.runModel()
FTR.generateImportantWords()


dbman.searchPerson(" ")
# you can specify other parameters to dbman
#def searchPerson(self, name, wordInSentence='', minimumdublicationProbability= 0,
#                     start_date = '1800-01-01', end_date = '3000-01-01')

debman.searchOrganization("")