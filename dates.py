from datetime import datetime
import json
from proxy import ProxyManager
import pandas as pd

class ScrapDates():

    url_dates = "https://www.europarl.europa.eu/plenary/en/ajax/getSessionCalendar.html?family=PV&termId={CurrentTerm}"
    directory_dates = 'dates/'

    def __init__(self, scrapDates=True, saveDates=True, currentTerm='9'):
        self.ProxyMana = ProxyManager()
        self.ListDate = []
        self.currentTerm = currentTerm
        self.Today = datetime.now().strftime("%d-%m-%Y")
        if scrapDates == True:
            self.scrapDates()
        if saveDates == True:
            self.saveDates()

    def scrapDates(self):
        dic_dates = self.ProxyMana.requestHandler(self.url_dates.replace('{CurrentTerm}', self.currentTerm)).content.decode('utf8').replace("'", '"')
        dic_dates = json.loads(dic_dates)
        # Process the answer to get a list of datetime, all date is contained in a list from sessionCalendar key
        self.ListDate = [datetime.strptime(i['day']+'-'+i['month']+'-'+i['year'], '%d-%m-%Y') for i in dic_dates['sessionCalendar']]

    def saveDates(self):
        # convert all dates to strings
        data_list = self.returnDates(type=[str])
        with open(self.directory_dates+self.Today+'.json', 'w+') as f:
            data = json.dumps(data_list)
            f.write(data)
    
    def returnDates(self, type=[list]):
        # Str allows to convert dates into str, while having a df regardless of the choice made on str or list
        data_toreturn = []
        if str in type:
            data_toreturn = [i.strftime('%d-%m-%Y') for i in self.ListDate]
        if list in type:
            data_toreturn = self.ListDate
        if type == "df":
            data_toreturn = pd.DataFrame({'Date': data_toreturn})
        return data_toreturn