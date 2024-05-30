import time
from dates import ScrapDates
from meps import ScrapMep
from datetime import datetime, timedelta
from votes import ScrapVotes
import json
from logManager import logManager
from proxy import ProxyManager
import requests

class ScrapPlanner():

    def __init__(self) -> None:

        self.Today = datetime.now().strftime("%d-%m-%Y")

        # When first launched, get the dates
        datesScrap = ScrapDates()
        dates = datesScrap.returnDates([str])
        self.sendRequest(date=self.Today, data=dates, typeData={'main': 'Dates'})

        # The try to scrap MEPs
        mepScrap = ScrapMep(processIncoming=True, processCurrent=True, processOutgoing=True)
        meps = mepScrap.returnMepList()
        self.sendRequest(date=self.Today, data=meps, typeData={'main': 'CurrentMEPs', 'subType': 'original'})

        # Get the votes of the last fifteen days for any correction
        self.votesCorrections(dates=dates)
        
        # Check if there is a vote today and try to get it 
        if self.Today in dates:
            self.launchVoteTask()    
    
    def launchVoteTask(self):
        isTrue = True
        time_to_sleep = 1200
        limit_time = self.Today+' 23:00:00'
        # Launch a loop that will launch every 20 minutes the job, and then every hour in case it gets a positive result
        while isTrue == True:
            if datetime.now() > datetime.strptime(limit_time, '%d-%m-%Y %H:%M:%S'):
                print('Breaking')
                isTrue = False
            
            returnValue = self.getVotes()
            
            if returnValue == True and time_to_sleep == 1200:
                time_to_sleep *= 4.5
            time.sleep(time_to_sleep)

    def getVotes(self):
        scrapVoteToday = ScrapVotes()
        if scrapVoteToday.returnTaskAchieved():
            data = scrapVoteToday.returnListVotes()
            self.sendRequest(self.Today, data=data, typeData={'main': 'ListVotes'})
            data = scrapVoteToday.returnMepsVotes()
            self.sendRequest(self.Today, data=data, typeData={'main': 'MepsVotes'})
            return True
        return False


    def sendRequest(self, date, data, typeData):
        # Make data a string
        r = {
            'Date': date,
            'Type': typeData,
            'Data': data
        }
        r = json.dumps(r)
        with open('test/'+typeData['main']+'.json', 'w+') as f:
            f.write(r)
        headers = {
            'Key': 'HELLO_WORLD',
            'Content-Type': 'application/json'
        }
        response = requests.post(url='http://127.0.0.1:5000/saver', json=r, headers=headers)
        print(response)
    
    def votesCorrections(self, dates):
        todayDate = datetime.now()
        startDate = todayDate - timedelta(days=40)
        matchingDates = [datetime.strptime(i, '%d-%m-%Y') for i in dates if startDate <= datetime.strptime(i, '%d-%m-%Y') < todayDate]
        # Check which dates were already processed
        already_processed = []
        try:
            with open('votes/votes_processed.json', 'r+') as f:
                already_processed = json.load(f)
        except Exception as e:
            logManager('Error', e)

        # For all dates within the range of 15 days, check for correction, if already processed do not try to get interinstitutional again
        for matching in matchingDates:
            if matching.strftime('%d-%m-%Y') in already_processed:
                scrapVotes = ScrapVotes(Date=matching, processInterinstitutional=False)
                data = scrapVotes.returnMepsVotes(condition={'Corrected': 'Yes'})
                self.sendRequest(matching.strftime('%d-%m-%Y'), data=data, typeData={'main': 'MepsVotes'})
            else:
                scrapVotes = ScrapVotes(Date=matching)
                data = scrapVotes.returnListVotes()
                self.sendRequest(matching.strftime('%d-%m-%Y'), data=data, typeData={'main': 'ListVotes'})
                data = scrapVotes.returnMepsVotes()
                self.sendRequest(matching.strftime('%d-%m-%Y'), data=data, typeData={'main': 'MepsVotes'})





