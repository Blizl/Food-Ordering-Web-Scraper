import requests 
import csv
read_file = open("Eat24_MA_V2.1.csv", "r")
reader = csv.reader(read_file)
row = next(reader)
url = row[2] + row[3]
print url
url2 = url.replace("\\","")
print url2
response = requests.get(url2)
print response.content
