import csv

read_file = open("grubhub_data_ma_with_menu_final.csv", "r")
reader = csv.reader(read_file)
read_file2 = open("zip_codes_states.csv", "r")
reader2 = csv.reader(read_file2)
write_file = open("grubhub_data_MA_with_menu_final_V2.csv", "w+")
writer = csv.writer(write_file)
zipcode_dict = dict()
for row in reader2:
    if row[4] == "MA":
        if len(row[0]) == 4:
            row[0] = "0" + row[0]
        zipcode_dict[row[3].lower()] = row[0]
print "Added to dict"
next(reader)
for row in reader:
    try:
        if "_" in row[3]:
            city = row[3].replace("_", " ")
        else:
            city = row[3]
        writer.writerow([row[0], row[1], row[2], city, zipcode_dict[city]])
    except IndexError:
        continue
