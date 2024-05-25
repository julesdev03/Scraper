import pandas as pd
from logManager import logManager

political_parties = {
    "Group of the European People's Party (Christian Democrats)": "EPP",
    "Identity and Democracy Group": "ID",
    "Group of the Greens/European Free Alliance": "Greens/EFA",
    "Group of the Progressive Alliance of Socialists and Democrats in the European Parliament": "S&D",
    "European Conservatives and Reformists Group": "ECR",
    "Renew Europe Group": "Renew",
    "The Left group in the European Parliament - GUE/NGL": "The Left",
    "Non-attached Members": "NI",
    "Group of the European United Left - Nordic Green Left": "The Left"
}


def MEP_Name_clean(input_Name):
    input_Name.lower()
    key = 0
    if "-" in input_Name:
        input_Name_split = input_Name.split("-")
        for keys in input_Name_split:
            input_Name_split[key] = input_Name_split[key].capitalize()
            key += 1
        input_Name = "-".join(input_Name_split)
        key = 0
        if " " in input_Name:
            input_Name_split = input_Name.split()
            for keys in input_Name_split:
                input_Name_split[key] = input_Name_split[key][:1].upper(
                ) + input_Name_split[key][1:]
                key += 1
            input_Name = " ".join(input_Name_split)
    elif " " in input_Name:
        input_Name_split = input_Name.split()
        for keys in input_Name_split:
            input_Name_split[key] = input_Name_split[key].capitalize()
            key += 1
        input_Name = " ".join(input_Name_split)
    return input_Name

def clean_text(input_text):
    input_text = input_text.replace("\n", "")
    input_text = input_text.replace("\t", "")
    return input_text.strip()

def saveAsCsv(data, fileName):
    try:
        df = pd.DataFrame.from_records(data)
        df.to_csv(fileName, index=False)
    except Exception as e:
        logManager('Error', str(e))