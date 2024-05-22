from datetime import datetime

class logManager():

    def __init__(self, type, info) -> None:
        timestamp = datetime.now()
        self.errorFile = "logs/"+timestamp.strftime("%d-%m-%Y")+".txt"
        self.RequestLogFile = "logs/RequestsLog/"+timestamp.strftime("%d-%m-%Y")+".txt"
        timeStampStr = "["+timestamp.strftime("%d-%m-%Y %H:%M:%S")+"]: "

        if type == "Error":
            try:
                with open(self.errorFile, 'a') as f:
                    f.write(timeStampStr+"\n"+info+"\n")
            except:
                pass
        
        if type == "RequestLog":
            with open(self.RequestLogFile, 'a') as f:
                # Write the date and time
                f.write(timeStampStr+"\n")
                # Write request code
                f.write("Status Code: "+str(info.status_code)+"\n")
                # Write the content
                f.write("Url: "+ info.url+"\n\n")

        