from flask import Flask, render_template, redirect, request, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Text, String, Integer
import csv
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# create the sqlalchemy object
db = SQLAlchemy(app)

global foodler_data
global eat24_menu
global eat24_data
global grubhub_data
'''TODO: 1. Pagnination widget is not responsive to all devices, need to fix in the future
         2. 404 web page needs to be created'''


class Restaurant(db.Model):
    __tablename__ = "Restaurants"
    link = db.Column(String(120), unique=False)
    name = db.Column(String(120), unique=False)
    menu = db.Column(Text, unique=False)
    zipcode = db.Column(String(32), unique=False)
    city = db.Column(String(120), unique=False)
    rest_id = db.Column(Integer, primary_key=True)

    def __init__(self, menu=None, link=None, name=None, zipcode=None, city=None, rest_id=None):
        self.name = name
        self.link = link
        self.menu = menu
        self.zipcode = zipcode
        self.city = city
        self.id = rest_id

    def __repr__(self):
        return '<Restaurant> %r' % (self.name)


def get_file_data(file_name):
    menu_dict = dict()
    if file_name == "Eat24_MA_with_menu.csv":
        with open(file_name, "r") as reader_file:
            reader = csv.reader(reader_file)
            for row in reader:
                menu_dict["/" + row[1]] = row[0]
            return menu_dict
    else:
        with open(file_name, 'rb') as reader_file:
            reader = csv.reader(reader_file)
            return list(reader)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/search', methods=['GET', 'POST'])
def search():
    search_query = request.form['search_query'].lower()
    session['query'] = search_query
    print search_query
    return redirect(url_for('search_results'))


@app.route('/search_results')
@app.route('/search_results?page=<int:page>')
def search_results(page=1):

    """TODO: If an empty string is thrown, should show correct webpage"""
    search_query = session['query']
    results = set()
    foodler_restaurants = set()
    grubhub_restaurants = set()
    eat24_restaurants = set()
    # for foodler_row in foodler_data:
    #     if search_query == foodler_row[2] or search_query == foodler_row[3] or search_query == foodler_row[4]:
    #         foodler_restaurants.add(foodler_row[2])
    for restaurant in Restaurant.query.filter_by(city=search_query).all():
        foodler_restaurants.add(restaurant.name)
    # for grubhub_row in grubhub_data:
    # if search_query == grubhub_row[0] or search_query == grubhub_row[1]:
    # results.setdefault(grubhub_row[1]).append(grubhub_row[2])
    # print eat24_data
    '''TODO: Need to fix issue when menu is too big, the menu continues onto the second line'''
    for grubhub_row in grubhub_data:
        try:
            if search_query == grubhub_row[2] or search_query == grubhub_row[3] or search_query == grubhub_row[4]:
                grubhub_restaurants.add(grubhub_row[2])
        except IndexError:
            continue
    for eat24_row in eat24_data:
        if search_query == eat24_row[2] or search_query == eat24_row[3] or search_query == eat24_row[4]:
            eat24_restaurants.add(eat24_row[2])
    results.update(foodler_restaurants)
    # results.update(grubhub_restaurants)
    # results.update(eat24_restaurants)


    page = request.args.get('page', type=int, default=1)
    pagination = Restaurant.query.filter_by(city=search_query).paginate(page, per_page=5)
    results = pagination.items
    return render_template("search.html", results=results, pagination=pagination,
                           search_query=search_query)


@app.route('/order_food/<result>')
def order_food(result):
    print "name of restaurant is", results


@app.before_first_request
def start():
    # global foodler_data
    # foodler_data = get_file_data("foodler_data_MA_with_menu_V2.csv")
    global eat24_menu
    eat24_menu = get_file_data("Eat24_MA_with_menu.csv")
    global eat24_data
    eat24_data = get_file_data("Eat24_MA_V2.3.csv")
    global grubhub_data
    grubhub_data = get_file_data("grubhub_data_MA_with_menu_final_V2.1.csv")


if __name__ == "__main__":
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run(debug=True)
