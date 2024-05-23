from proxy import ProxyManager
from logManager import logManager
from datetime import datetime
import re
import xml.etree.ElementTree as ET
import pandas as pd
import os

class ScrapVotes():
    url_vote = 'https://www.europarl.europa.eu/doceo/document/PV-9-{date}-RCV_EN.xml'
    alt_url_vote = 'https://www.europarl.europa.eu/doceo/document/PV-9-{date}-RCV_FR.xml'
    file_path = 'votes/VOTE-{date}.xml'
    votes_directory = 'votes/'

    def __init__(self, Date=None) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        # If no date inserted, download today
        if Date == None:
            self.Date = today
        else:
            self.Date = Date.strftime('%Y-%m-%d')
        self.ProxyMana = ProxyManager()
    
    def getVote(self):
        try:
            # Try first the url for FR xml
            url = self.url_vote.replace('{date}', self.Date)
            r = self.ProxyMana.requestHandler(url)
            open(self.file_path.replace("{date}", self.Date), "wb").write(r.content)
        except:
            try:
                # Try with EN xml
                alt_url = self.alt_url_vote.replace('{date}', self.Date)
                r = self.ProxyMana.requestHandler(alt_url)
                open(self.file_path.replace("{date}", self.Date), "wb").write(r.content)
            except:
                pass
    
    def getType(self, RcvDescription):
        try:
            # Manage when it is an agenda vote
            if "Ordre du jour" in RcvDescription:
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
            if "Ordre du jour" in RcvDescription:
                return "Agenda"
        except:
            pass
        return None
    
    def processVote(self):
        # Parse votes in XML with myroot
        try:
            myroot = ET.parse(self.file_path.replace("{date}", self.Date)).getroot()
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
                                # Append the vote
                                listMepsVotes.append({'PersId': meps.get("PersId"), 'Identifier': UniqueIdentifier, 'Vote':'For', 'Corrected':'No'})
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # In the xml, get the results against, then parse the tree to the groups and to the individual MEPs
                    resultAgainst = vote.find('Result.Against')
                    Against = resultAgainst.get('Number')
                    if resultAgainst:
                        for groups in resultAgainst.findall("Result.PoliticalGroup.List"):
                            for meps in groups.findall("PoliticalGroup.Member.Name"):
                                # Append the vote
                                listMepsVotes.append({'PersId': meps.get("PersId"), 'Identifier': UniqueIdentifier, 'Vote':'Against', 'Corrected':'No'})
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # In the xml, get the results abstention, then parse the tree to the groups and to the individual MEPs
                    resultAbstention = vote.find('Result.Abstention')
                    Abstention = resultAbstention.get('Number')
                    if resultAbstention:
                        for groups in resultAbstention.findall("Result.PoliticalGroup.List"):
                            for meps in groups.findall("PoliticalGroup.Member.Name"):
                                # Append the vote
                                listMepsVotes.append({'PersId': meps.get("PersId"), 'Identifier': UniqueIdentifier, 'Vote':'Abstention', 'Corrected':'No'})
                except Exception as e:
                    logManager('Error', str(e))
                
                try:
                    # Get the votes corrections, but keep the count of votes intact
                    intention = vote.find('Intentions')
                    for intentionTypes in intention:
                        vote = intentionTypes.tag.split('.')[-1]
                        for meps in intentionTypes:
                            PersId = meps.get('PersId')
                            # Get the MEP matching the values and change his vote
                            indexMepMatching = [i for i, d in enumerate(listMepsVotes) if PersId and UniqueIdentifier in d.values()][0]
                            listMepsVotes[indexMepMatching]['Vote'] = vote
                            listMepsVotes[indexMepMatching]['Corrected'] = 'Yes'
                except:
                    pass

                # Append the list of votes
                listVotes.append({'Identifier': UniqueIdentifier, 'FileNumber': FileNumber, 'Date': self.Date, 'Type':voteType, 'Title':RcvDescription, 'InterinstitutionalNumber':'', 'For':For, 'Against':Against, 'Abstention':Abstention})

                # Try to save as csv
            try:
                dflistVotes = pd.DataFrame.from_records(listVotes)
                dflistMepsVotes = pd.DataFrame.from_records(listMepsVotes)
                dflistMepsVotes.to_csv(self.votes_directory+self.Date+'_meps_vote'+'.csv', index=False)
                dflistVotes.to_csv(self.votes_directory+self.Date+'_list_vote'+'.csv', index=False)
            except Exception as e:
                logManager('Error', str(e))
        except Exception as e:
            logManager('Error', str(e))
        
        self.deleteVoteFiles()
    
    def deleteVoteFiles(self):
        os.remove(self.file_path.replace('{date}', self.Date))
                
        
