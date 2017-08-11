from hello import db
from models import Restaurant
import csv

db.create_all()

read_file = open("foodler_data_MA_with_menu_V2.1.csv", "r")
reader = csv.reader(read_file)
next(reader)
for row in reader:
    db.session.add(Restaurant(row[0], row[1], row[2], row[3], row[4], int(row[5])))

db.session.commit()
