import subprocess
import requests
import random
from logManager import logManager

class ProxyManager():
    countries = ['US', 'FR', 'BE', 'DE', 'GB', 'FI', 'GR', 'HR', 'HU', 'DK', 'EE']
    proxyCountFile = "proxy_count.txt"

    def __init__(self) -> None:
        self.checkCount()
        isActive = self.checkIfActive()
        if isActive == False:
            self.changeIp()

    def checkCount(self):
        # Try to get the value, if can not be translated into into int then it equals 0
        # Else create file
        try:
            with open(self.proxyCountFile, "r+") as f:
                try:
                    self.requestsCount = int(f.read())
                except:
                    self.requestsCount = 0
        except:
            with open(self.proxyCountFile, "w+") as f:
                f.write(str(0))

    def appendCount(self):
        # Check if it is the 30st request, then change the proxy if that is the case
        self.requestsCount += 1
        if self.requestsCount > 30:
            self.changeIp()
            self.requestsCount = 0
        # Overwrite the file with the new value
        with open(self.proxyCountFile, "w+") as f:
            f.write(str(self.requestsCount))

    def checkIfActive(self):
        ToCheck = subprocess.check_output('cyberghostvpn --status', shell=True).decode('utf8').replace("'", '"')
        if "No VPN connections found" in ToCheck:
            return False
        return True

    def requestHandler(self, url, parameters=""):
        self.appendCount()
        try:
            request = requests.get(url, params=parameters, allow_redirects=True)
            # Request registry
            logManager('RequestLog', request)
            if request.status_code == 200:
                return request
            request.raise_for_status()
        except Exception as e:
            # Write the error
            logManager('Error', str(e))
            raise Exception('Error')

    def changeIp(self):
        randomCountry = random.choice(self.countries)
        subprocess.run(f'sudo cyberghostvpn --country-code {randomCountry} --connect', shell=True)