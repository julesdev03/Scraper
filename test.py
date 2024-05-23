from proxy import ProxyManager
from votes import ScrapVotes
from datetime import datetime

scraper = ScrapVotes(Date=datetime.strptime('24/04/2024', '%d/%m/%Y'))
scraper.getVote()
scraper.processVote()