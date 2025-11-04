import requests
import zipfile
import os
import pandas as pd

def get_file(url):
    zip = requests.get(url).content
    with open("drug.zip", 'wb') as f:
        f.write(zip)

def unzip(file):
    with zipfile.ZipFile(file) as zObj:
        zObj.extractall("./")

def get_drug_data():
    if "drug.zip" not in os.listdir(): 
        print("Fetching Zip file")
        get_file("https://archive.ics.uci.edu/static/public/461/drug+review+dataset+druglib+com.zip")
    if "drugLibTrain_raw.tsv" not in os.listdir():
        print("Unzipping File")
        unzip("drug.zip")
    df = pd.read_csv("drugLibTrain_raw.tsv", sep="\t")
    cols = ["benefitsReview", "sideEffectsReview", "commentsReview"]
    data = []
    for col in cols:
        assert not df[col].empty
        data.append(df[col].tolist())
    bsc = (data[0], data[1], data[2]) 
    return bsc

if __name__ == "__main__":
    print(get_drug_data())