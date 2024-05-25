from datetime import datetime, date
import xml.etree.ElementTree as ET
import os
from proxy import ProxyManager
from logManager import logManager
from general_functions import *
import json

class ScrapMep():
    url_current = 'https://www.europarl.europa.eu/meps/en/full-list/xml/'
    url_incoming = 'https://www.europarl.europa.eu/meps/en/incoming-outgoing/incoming/xml'
    url_outgoing = 'https://www.europarl.europa.eu/meps/en/incoming-outgoing/outgoing/xml'
    list_meps = []
    directory_name = 'meps/'
    url_picture_mep = "https://www.europarl.europa.eu/mepphoto/{PersId}.jpg"

    def __init__(self, processIncoming=True, processCurrent=True, processOutgoing=True, getPicture=True) -> None:
        self.ProxyMana = ProxyManager()
        today = datetime.now().strftime("%d-%m-%Y")
        self.Today = today
        
        if processIncoming == True:
            # Get the file of the incoming
            self.downloadMepsFile(type='incoming')
            # Process the incoming only to retain PersId and entry date
            self.incomingMepsProcess()
            # Delete the file
            os.remove(self.directory_name+"incoming.xml")
        
        if processCurrent == True:
            # Get the file
            self.downloadMepsFile(type='current')
            # Process the current meps
            self.currentMepsProcess()
            # Delete the file
            os.remove(self.directory_name+"current.xml")

        if processOutgoing == True:
            # Get the file
            self.downloadMepsFile(type='outgoing')
            # Process outgoing meps
            self.outgoingMepsProcess()
            # Delete the file
            os.remove(self.directory_name+"outgoing.xml")
        
        if getPicture == True and processCurrent == True:
            self.downloadPictures()

    def outgoingMepsProcess(self):
        try:
            myroot = ET.parse(self.directory_name+'outgoing.xml').getroot()
            # Get all meps and parse them
            for mep in myroot.findall('mep'):
                # Get the name
                Name = MEP_Name_clean(clean_text(mep.find('fullName').text))
                # Get the country
                Country = clean_text(mep.find('country').text)
                # Get the PersId
                PersId = clean_text(mep.find('id').text)
                # Get the EuParty
                EuParty = clean_text(political_parties[mep.find('politicalGroup').text])
                # NationalParty
                NationalParty = clean_text(mep.find('nationalPoliticalGroup').text)
                # Default leave date
                LeaveDate = datetime.strptime(mep.find('mandate-end').text, '%d/%m/%Y')
                # Check for an entry date, otherwise default
                EntryDate = datetime.strptime(mep.find('mandate-start').text, '%d/%m/%Y')
                # Append to list Meps
                self.list_meps.append({"PersId":PersId, "Name":Name, "EuParty":EuParty, "Country":Country, "NationalParty":NationalParty, "LeaveDate":LeaveDate, "EntryDate":EntryDate})
        except Exception as e:
            logManager('Error', e, additional_data='OUTGOING MEPs')

    def incomingMepsProcess(self):
        try:
            myroot = ET.parse(self.directory_name+'incoming.xml').getroot()
            list_ = []
            # Get all meps and parse them
            for mep in myroot.findall('mep'):
                # Get the PersId
                PersId = clean_text(mep.find('id').text)
                # Entry date
                date = clean_text(mep.find('mandate-start').text).replace('/', '-')
                EntryDate = datetime.strptime(date, "%d-%m-%Y")
                # Append to list Meps
                list_.append({"PersId":PersId, "EntryDate":EntryDate})
            self.incoming = list_
        except Exception as e:
            logManager('Error', e, additional_data='INCOMING MEPS')

    def currentMepsProcess(self):
        try:
            myroot = ET.parse(self.directory_name+'current.xml').getroot()
            list_ = []
            # Get all meps and parse them
            for mep in myroot.findall('mep'):
                # Get the name
                Name = MEP_Name_clean(clean_text(mep.find('fullName').text))
                # Get the country
                Country = clean_text(mep.find('country').text)
                # Get the PersId
                PersId = clean_text(mep.find('id').text)
                # Get the EuParty
                EuParty = clean_text(political_parties[mep.find('politicalGroup').text])
                # NationalParty
                try:
                    NationalParty = clean_text(mep.find('nationalPoliticalGroup').text)
                except:
                    NationalParty = EuParty
                # Default leave date
                LeaveDate = "ongoing"
                # Check for an entry date, otherwise default
                EntryDate=''
                try:
                    if self.incoming:
                        for els in self.incoming:
                            if els['PersId'] == PersId:
                                EntryDate = els['EntryDate']
                except:
                    pass
                if EntryDate=='':
                    EntryDate = '02-06-2019'
                # Append to list Meps
                self.list_meps.append({"PersId":PersId, "Name":Name, "EuParty":EuParty, "Country":Country, "NationalParty":NationalParty, "LeaveDate":LeaveDate, "EntryDate":EntryDate})
            saveAsCsv(data=self.list_meps, fileName=self.directory_name+self.Today+'_current.csv')
        except Exception as e:
            logManager('Error', e ,additional_data="CURRENT MEPs")

    def downloadMepsFile(self, type):
        try:
            if type=='incoming':
                r = self.ProxyMana.requestHandler(self.url_incoming)
            if type=='current':
                r = self.ProxyMana.requestHandler(self.url_current)
            if type=='outgoing':
                r = self.ProxyMana.requestHandler(self.url_outgoing)
            open(self.directory_name+type+'.xml', "wb").write(r.content)
        except:
            pass
    
    def downloadPictures(self):
        # Get the list of already existing pictures
        list_files = os.listdir('meps/pictures')
        listPersId = []
        for els in list_files:
            els = els[:-4]
            listPersId.append(els)
        # Get the list of non existent pictures
        not_existent = [i['PersId'] for i in self.list_meps if i['PersId'] not in listPersId]
        listNewPictures = []
        # Get the pictures
        for PersId in not_existent:
            url = self.url_picture_mep.replace('{PersId}', PersId)
            path = self.directory_name+'pictures/'+PersId+'.jpg'
            try:
                r = self.ProxyMana.requestImageHandler(url, path)
                listNewPictures.append(PersId)
            except:
                pass
        self.addToListPicturesrocessed(listNewPictures)
    
    def addToListPicturesrocessed(self, listNewPictures):
        # Overwrite the file
        with open(self.directory_name+'new_pictures.json', 'w+') as f:
            f.write(json.dumps(listNewPictures))


