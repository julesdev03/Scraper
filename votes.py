from proxy import ProxyManager
from logManager import logManager
from datetime import datetime
import re
import xml.etree.ElementTree as ET
import os
from bs4 import BeautifulSoup
import json
from general_functions import *

class ScrapVotes():
    url_vote = 'https://www.europarl.europa.eu/doceo/document/PV-9-{date}-RCV_EN.xml'
    alt_url_vote = 'https://www.europarl.europa.eu/doceo/document/PV-9-{date}-RCV_FR.xml'
    file_path = 'votes/VOTE-{date}.xml'
    votes_directory = 'votes/'
    url_file = "https://www.europarl.europa.eu/doceo/document/{file_number}_EN.html"

    def __init__(self, Date=None, downloadVote=True, processVote=True, processInterinstitutional=True) -> None:
        self.Today = datetime.now()
        # If no date inserted, download today
        if Date == None:
            self.Date = self.Today
        else:
            self.Date = Date
        self.ProxyMana = ProxyManager()

        # Make the steps based on the input
        if downloadVote == True:
            self.getVote()
        if processVote == True:
            self.processVote()
        # Can not process interinstitutional without processing the vote get the data
        if processInterinstitutional == True and processVote == True:
            self.getInterinstitutionalFileNumber()
        # If everything is processed, add to the list of already processed files
        if downloadVote == True and processVote == True and processInterinstitutional == True:
            self.addToListAlreadyProcessed()
    
    def returnMepsVotes(self, condition=None):
        # Possibility to return only when one column has a specific value
        votes = self.listMepsVotes
        if type(condition) is dict:
            votes = [i for i in votes if i[list(condition.keys())[0]] == condition[list(condition.keys())[0]]]
        return votes
    
    def returnTaskAchieved(self):
        return self.taskAchieved
    
    def returnListVotes(self):
        return self.listVotes

    def addToListAlreadyProcessed(self):
        listDates = []
        date = self.Date.strftime('%d-%m-%Y')
        # Get the list in the file if the file exists
        try:
            with open(self.votes_directory+'votes_processed.json') as f:
                    listDates = json.load(f)
        except:
            pass
        # Append the list regardless of whether it previously existed
        if date not in listDates:
            listDates.append(date)
        # Overwrite the file
        with open(self.votes_directory+'votes_processed.json', 'w+') as f:
            f.write(json.dumps(listDates))

    def getVote(self):
        try:
            # Try first the url for FR xml
            url = self.url_vote.replace('{date}', self.Date.strftime('%Y-%m-%d'))
            r = self.ProxyMana.requestHandler(url)
            open(self.file_path.replace("{date}", self.Date.strftime('%d-%m-%Y')), "wb").write(r.content)
        except:
            try:
                # Try with EN xml
                alt_url = self.alt_url_vote.replace('{date}', self.Date.strftime('%Y-%m-%d'))
                r = self.ProxyMana.requestHandler(alt_url)
                open(self.file_path.replace("{date}", self.Date.strftime('%d-%m-%Y')), "wb").write(r.content)
            except:
                pass
    
    def getType(self, RcvDescription):
        try:
            # Manage when it is an agenda vote
            if "Ordre du jour" in RcvDescription or self.checkIfAgenda(RcvDescription):
                # Dots or dash
                if re.search("[a-z]{5,8}:", str(RcvDescription), re.IGNORECASE):
                    return RcvDescription.split(':')[1].strip() + " - " + RcvDescription.split(":")[0].strip()
                elif re.search('[a-z]{5,8} -', str(RcvDescription), re.IGNORECASE):
                    return RcvDescription.split('-')[1].strip() + " - " + RcvDescription.split("-")[0].strip()
        except:
            pass
        try:
            typeVote = RcvDescription.split('–')[-1].strip()
            return typeVote
        except:
            pass
        try:
            # Regular AM or any other description after the last dash
            typeVote = RcvDescription.split("-")[-1].strip()
            return typeVote
        except:
            # If none of these categories just return the full name stripped
            return RcvDescription.strip()

    def getFileNumber(self, RcvDescription):
        try:
            # Regular file number
            searchFile = re.search("[A-C][0-9]{1,2}-[0-9]{4}/[0-9]{4}", str(RcvDescription), re.IGNORECASE)
            if searchFile:
                return searchFile.group()
        except:
            pass
        try:
            # Resolution number
            searchResol = re.search("RC-[A-C][0-9]{1,2}-[0-9]{4}/[0-9]{4}", str(RcvDescription), re.IGNORECASE)
            if searchResol:
                return searchResol.group()
        except:
            pass
        try:
            # Not sure it still exists
            searchAltFile = re.search("[A-C]-[0-9]{1,2}-[0-9]{4}/[0-9]{4}", str(RcvDescription), re.IGNORECASE)
            if searchAltFile:
                return searchAltFile.group()
        except:
            pass
        try:
            if "Ordre du jour" in RcvDescription or self.checkIfAgenda(RcvDescription):
                return "Agenda"
        except:
            pass
        return ''

    def checkIfAgenda(self, title):
        if 'agenda' in title:           
            if [i for i in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] if i in title]:
                return True
        return False
    
    def processVote(self):
        # Parse votes in XML with myroot
        try:
            myroot = ET.parse(self.file_path.replace("{date}", self.Date.strftime('%d-%m-%Y'))).getroot()
            # List of votes
            listVotes = []
            # List of MEPs votes
            listMepsVotes = []
            for vote in myroot.findall('RollCallVote.Result'):
                # Get Description of the vote as a string
                RcvDescription = ET.tostring(vote.find("RollCallVote.Description.Text"), method='text', encoding="unicode")
                # Get vote identifier 
                UniqueIdentifier = vote.get('Identifier')
                # Get FileNumber if present otherwise = None
                FileNumber = self.getFileNumber(RcvDescription)
                # Get type of vote (usually amendment)
                voteType = self.getType(RcvDescription)
                # Set up the vote counters
                For = 0
                Against = 0
                Abstention = 0

                try:
                    # In the xml, get the results for, then parse the tree to the groups and to the individual MEPs
                    resultFor = vote.find('Result.For')
                    For = resultFor.get('Number')
                    if resultFor:
                        for groups in resultFor.findall("Result.PoliticalGroup.List"):
                            for meps in groups.findall("PoliticalGroup.Member.Name"):
                                try:
                                    # Append the vote
                                    listMepsVotes.append({'PersId':meps.get("PersId"),'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'For', 'Corrected':'No'})
                                except:
                                    listMepsVotes.append({'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'For', 'Corrected':'No'})
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # In the xml, get the results against, then parse the tree to the groups and to the individual MEPs
                    resultAgainst = vote.find('Result.Against')
                    Against = resultAgainst.get('Number')
                    if resultAgainst:
                        for groups in resultAgainst.findall("Result.PoliticalGroup.List"):
                            for meps in groups.findall("PoliticalGroup.Member.Name"):
                                try:
                                    # Append the vote
                                    listMepsVotes.append({'PersId':meps.get("PersId"),'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'Against', 'Corrected':'No'})
                                except:
                                    listMepsVotes.append({'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'Against', 'Corrected':'No'})
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # In the xml, get the results abstention, then parse the tree to the groups and to the individual MEPs
                    resultAbstention = vote.find('Result.Abstention')
                    Abstention = resultAbstention.get('Number')
                    if resultAbstention:
                        for groups in resultAbstention.findall("Result.PoliticalGroup.List"):
                            for meps in groups.findall("PoliticalGroup.Member.Name"):
                                # Create dictionary with all element, if PersId exists, append dict
                                try:
                                    # Append the vote
                                    listMepsVotes.append({'PersId':meps.get("PersId"),'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'Abstention', 'Corrected':'No'})
                                except:
                                    listMepsVotes.append({'MepId':meps.get('MepId'), 'Identifier': UniqueIdentifier, 'Vote':'Abstention', 'Corrected':'No'})
                                
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # Get the votes corrections, but keep the count of votes intact
                    intention = vote.find('Intentions')
                    for intentionTypes in intention:
                        vote = intentionTypes.tag.split('.')[-1]
                        for meps in intentionTypes:
                            MepId = meps.get('MepId')
                            # Get the MEP matching the values and change his vote
                            indexMepMatching = [i for i, d in enumerate(listMepsVotes) if str(MepId) == str(d['MepId']) and str(UniqueIdentifier) == str(d['Identifier'])]
                            # Take into consideration possibilities of having no match or several matches
                            if len(indexMepMatching) == 1:
                                indexMepMatching = indexMepMatching[0]
                                listMepsVotes[indexMepMatching]['Vote'] = vote
                                listMepsVotes[indexMepMatching]['Corrected'] = 'Yes'                           
                except Exception as e:
                    pass

                # Append the list of votes
                listVotes.append({'Identifier': UniqueIdentifier, 'FileNumber': FileNumber, 'Date': self.Date.strftime('%d-%m-%Y'), 'Type':voteType, 'Title':RcvDescription, 'InterinstitutionalNumber':'', 'For':For, 'Against':Against, 'Abstention':Abstention})
            # Try to save as csv
            self.listVotes = listVotes
            self.listMepsVotes = listMepsVotes
            saveAsCsv(data=listMepsVotes, fileName=self.votes_directory+self.Date.strftime('%d-%m-%Y')+'_meps_vote_processed_'+self.Today.strftime('%d-%m-%Y')+'.csv')
            saveAsCsv(data=self.listVotes, fileName=self.votes_directory+self.Date.strftime('%d-%m-%Y')+'_list_vote_processed_'+self.Today.strftime('%d-%m-%Y')+'.csv')
            self.taskAchieved = True
        except Exception as e:
            logManager('Error', str(e))
        
        self.deleteVoteFiles()

    def deleteVoteFiles(self):
        os.remove(self.file_path.replace('{date}', self.Date.strftime('%d-%m-%Y')))
    
    def getTermInFileNumber(self, string):
        numbers = ''
        alphabets = '' 
        # Iterate through each character in the given string
        for char in string:
            # Check if the character is an alphabet
            if char.isalpha():
                # If it is an alphabet, append it to the alphabets string
                alphabets += char
            # Check if the character is a number
            elif char.isnumeric():
                # If it is a number, append it to the numbers string
                numbers += char
        return numbers

    def buildUrlFile(self, fileNumber):
        # Take the different file number possibilities and adapt it for the url (A, B, RC-B)
        try:
            if fileNumber == "Agenda":
                return None
            # Get the file number for the url for report (A), resolution (B) or (C) probably objection
            elif fileNumber[:1] in ['A', 'B', 'C']:
                split_file = fileNumber.split('-')
                term = self.getTermInFileNumber(split_file[0])
                number, year = split_file[1].split('/')
                finalNumber = f"{fileNumber[:1]}-{term}-{year}-{number}"
            # Same but for joint motion for resolution (RC)
            elif fileNumber[:2] == 'RC':
                split_file = fileNumber.split('-')
                term = self.getTermInFileNumber(split_file[1])
                number, year = split_file[2].split('/')
                finalNumber = f"RC-{term}-{year}-{number}"
            else:
                return None
            toReturn = self.url_file.replace('{file_number}', finalNumber)
            return toReturn
        except Exception as e:
            try:
                logManager('Error', e, "PROCESS: buildUrlFile(); FILE_NUMBER: "+fileNumber)
            except:
                logManager('Error', e, "PROCESS: buildUrlFile(); FILE_NUMBER: NOT PROCESSABLE")


    def getInterinstitutionalFileNumber(self):
        # Get a list of unique fileNumbers
        listFiles = []
        # Dictionary equivalence
        equivalence = {}
        # get interinstitutional file number per file
        for file in self.listVotes:
            # Check if file number already processed
            if file['FileNumber'] not in listFiles:
                try:
                    # Get the html, parse it
                    url = self.buildUrlFile(file['FileNumber'])
                    # If the file number was not planned, then it returns none so skip that file
                    if url == None:
                        continue
                    fp = self.ProxyMana.requestHandler(url).text
                    soup = BeautifulSoup(fp, "html.parser")
                    # Contained in a p element with a unique class, inside an a element after that
                    getThePElement = soup.find("p", class_="m-lg-0")
                    # Get the last one to avoid getting the COM proposal when it appears
                    aElement = getThePElement.find_all("a")[-1]
                    InterinstitutionalNumber = aElement.text
                    equivalence[file['FileNumber']] = InterinstitutionalNumber
                    # Edit the dict
                    file['InterinstitutionalNumber'] = InterinstitutionalNumber
                    listFiles.append(file['FileNumber'])
                except:
                    pass                
            else:
                # If there is an equivalent 
                file['InterinstitutionalNumber'] = equivalence[file['FileNumber']]
        # Save as csv
        saveAsCsv(data=self.listVotes, fileName=self.votes_directory+self.Date.strftime('%d-%m-%Y')+'_list_vote_processed_'+self.Today.strftime('%d-%m-%Y')+'.csv')
                
        
