import scrapy
from RestaurantScraper.items import RestaurantInfoItem, MenuItem
import json
import csv


class GrubhubSpider(scrapy.Spider):
    name = "grubhub_v2"
    '''Access token is found by manually looking at headers of grubhub'''
    headers = {'Authorization': 'Bearer 56a3e784-dc0c-49c3-a08d-d6e3cb30f4ff'}

    def start_requests(self):
        grubhub_file = open("grubhub_data_MA_with_menu_final_V2.csv", "r")
        reader = csv.reader(grubhub_file)
        restaurant_ids = set()
        for row in reader:
            restaurant_ids.add(self.get_restaurant_id(row[1]))
        for restaurant_id in restaurant_ids:
            print "Starting restaurant_id ", restaurant_id
            url = ("https://api-gtm.grubhub.com/restaurants/" + restaurant_id +
                   "?hideChoiceCategories=true&hideUnavailableMenuItems=true&" +
                   "hideMenuItems=false&showMenuItemCoupons=false")
            yield scrapy.Request(url=url, callback=self.parse_menu, headers=self.headers)
        grubhub_file.close()

    def parse_menu(self, response):
        restaurant_data = json.loads(response.body)
        restaurant_id = restaurant_data['restaurant']['id']
        menu_item = MenuItem()
        menu_category_list = restaurant_data['restaurant']['menu_category_list']
        menu_item['provider'] = "grubhub"
        menu_item['restaurant_id'] = restaurant_id
        menu_item['additional'] = {}  # Should be empty but added to make data consistent
        for i in range(len(menu_category_list)):
            for j in range(len(menu_category_list[i]['menu_item_list'])):
                menu_item['name'] = menu_category_list[i]['menu_item_list'][j]['name']
                item_id = menu_category_list[i]['menu_item_list'][j]['id']
                menu_item['price'] = self.convertPrice(menu_category_list[i]['menu_item_list'][j]['price']['amount'])
                minimum_price_variation = menu_category_list[i]['menu_item_list'][j]['minimum_price_variation']
                maximum_price_variation = menu_category_list[i]['menu_item_list'][j]['maximum_price_variation']
                modal_url = "https://api-gtm.grubhub.com/restaurants/" + restaurant_id + "/menu_items/" + item_id
                if minimum_price_variation != maximum_price_variation:
                    request = scrapy.Request(url=modal_url, callback=self.parse_modal, headers=self.headers)
                    request.meta['restaurant_id'] = restaurant_id
                    yield request
                else:
                    yield menu_item

    def parse_modal(self, response):
        item_data = json.loads(response.body)
        menu_item = MenuItem()
        item_name = self.removePeriodsFromString(item_data['name'])
        menu_item['provider'] = "grubhub"
        menu_item['restaurant_id'] = response.meta['restaurant_id']
        menu_item['price'] = self.convertPrice(item_data['minimum_price_variation']['amount'])
        choice_category_list = item_data['choice_category_list']
        if choice_category_list[0]['name'] == "Choose a size":
            first_choice_option_list = choice_category_list[0]['choice_option_list']
            for i in range(len(first_choice_option_list)):
                # size_price = self.convertPrice(first_choice_option_list[i]['price']['amount'])
                # size_name = item_name + " " + first_choice_option_list[i]['description']
                menu_item['name'] = item_name + " " + first_choice_option_list[i]['description']
                menu_item['price'] = self.convertPrice(first_choice_option_list[i]['price']['amount'])
                menu_item['additional'] = {}
                for j in range(1, len(choice_category_list)):
                    choice_option_list = choice_category_list[j]['choice_option_list']
                    additional_items_per_size = self.get_additional_items(choice_option_list, i)
                    menu_item['additional'].update(additional_items_per_size)
                yield menu_item
        else:
            # additional_items = {}
            menu_item['name'] = item_name
            menu_item['additional'] = {}
            for k in range(len(choice_category_list)):
                choice_option_list = choice_category_list[k]['choice_option_list']
                for choice_option in choice_option_list:
                    additional_item_name = self.removePeriodsFromString(choice_option['description'])
                    additional_item_price = self.convertPrice(choice_option['price']['amount'])
                    # additional_items.update({additional_item_name: additional_item_price})
                    menu_item['additional'].update({additional_item_name: additional_item_price})
            # item['menu'].update({item_name: {"price": item_price, "additional": additional_items}})
            yield menu_item

    def convertPrice(self, price):
        price = str(price)
        if price == "0":
            price = "$0.00"
            return price
        price = price[:-2] + "." + price[-2:]
        if price[0] == ".":
            price = "$0" + price
        else:
            price = "$" + price
        return price

    def get_additional_items(self, choice_option_list, size_index):
        additional_items = {}
        for i in range(len(choice_option_list)):
            additional_item_name = self.removePeriodsFromString(choice_option_list[i]['description'])
            if choice_option_list[i]['price_changes']:
                price_changes_keys = choice_option_list[i]['price_changes'].keys()
                price_change_amt = choice_option_list[i]['price_changes'][price_changes_keys[size_index]]['amount']
                additional_item_price = self.convertPrice(price_change_amt)
                additional_items.update({additional_item_name: additional_item_price})
            else:
                additional_item_price = self.convertPrice(choice_option_list[i]['price']['amount'])
                additional_items.update({additional_item_name: additional_item_price})
        return additional_items

    def get_restaurant_id(self, link):
        reversed_url = link[::-1]
        restaurant_id = reversed_url[:reversed_url.find("/")][::-1]
        return restaurant_id

    def removePeriodsFromString(self, string):
        new_string = string.replace(".", " ")
        return new_string
