from proxy import ProxyManager
from votes import ScrapVotes
from datetime import datetime
import requests
from bs4 import BeautifulSoup

scraper = ScrapVotes(Date=datetime.strptime('25/04/2024', '%d/%m/%Y'))
# scraper.getVote()
# scraper.processVote()


# A-9-2024-0183
# RC-9-2024-0227

# A9-0163/2024
# B9-0225/2024

# def getTermInFileNumber(string):
#     numbers = ''
#     alphabets = '' 
#     # Iterate through each character in the given string
#     for char in string:
#         # Check if the character is an alphabet
#         if char.isalpha():
#             # If it is an alphabet, append it to the alphabets string
#             alphabets += char
#         # Check if the character is a number
#         elif char.isnumeric():
#             # If it is a number, append it to the numbers string
#             numbers += char
#     return numbers

# def buildUrlFile(fileNumber):
#     url_file = "https://www.europarl.europa.eu/doceo/document/{file_number}_EN.html"
#     if fileNumber[:1] == 'A':
#         split_file = fileNumber.split('-')
#         term = getTermInFileNumber(split_file[0])
#         number, year = split_file[1].split('/')
#         finalNumber = f"A-{term}-{year}-{number}"
#     elif fileNumber[:1] == 'B':
#         split_file = fileNumber.split('-')
#         term = getTermInFileNumber(split_file[0])
#         number, year = split_file[1].split('/')
#         finalNumber = f"B-{term}-{year}-{number}"
#     elif fileNumber[:2] == 'RC':
#         split_file = fileNumber.split('-')
#         print(split_file)
#         term = getTermInFileNumber(split_file[1])
#         number, year = split_file[2].split('/')
#         finalNumber = f"RC-{term}-{year}-{number}"
#     else:
#         finalNumber = ''
#     toReturn = url_file.replace('{file_number}', finalNumber)
#     return toReturn

# url = buildUrlFile('RC-B9-0227/2024')
# fp = requests.get(url).text
# soup = BeautifulSoup(fp, "html.parser")
# getThePElement = soup.find("p", class_="m-lg-0")
# aElement = getThePElement.find("a")
# file = aElement.text
#     # Get a element for the MEP box 
#     MEPBox = soup.find_all("a", class_="erpl_member-list-item-content mb-3 t-y-block")

#     dic_number_name = OrderedDict()
#     # dic_MEP_info = {}
#     list_MEP = []
#     count = 0
#     for els in MEPBox:
#         print(count)
#         count += 1
#         url = els.get('href')
#         MEPNumber = url.split("/")[-1]
#         name = MEP_name_clean(els.find("div", class_="erpl_title-h4 t-item").text)
