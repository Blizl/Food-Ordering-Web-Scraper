import ast
import json
import re
import scrapy
from RestaurantScraper.items import RestaurantInfoItem, MenuItem
from bs4 import BeautifulSoup


"""
    TODO: Bug List:
    1. Some restaurant names/zipcodes are missing but menu is being scrape
    2. When scraped, some items have two prices, one for small, one for large, create a seperate entry for each instead
    of one combined item
    3. When added a topping that shows up twice with different prices, find a way to append to dictionary
"""


class FoodlerSpider(scrapy.Spider):
    """This spider returns the menu items within each menu"""
    name = "foodler_menu_spider"
    provider = "foodler"
    start_urls = [
        "https://www.foodler.com/"
    ]
    visited_urls = set()

    def start_requests(self):
        """TODO: in the future, need to extend the zipcodes to all of USA"""
        first_state_zipcode = 1001
        last_state_zipcode = 1002
        foodler_base_url = "https://www.foodler.com/"
        for zipcode in range(first_state_zipcode, last_state_zipcode):
            if len(str(zipcode)) == 4:
                zipcode_str = "0" + str(zipcode)
            else:
                zipcode_str = str(zipcode)
            print "zipcode is %s" % zipcode_str
            print "From startRequest, link is ", foodler_base_url + zipcode_str
            yield scrapy.Request(foodler_base_url + zipcode_str, callback=self.parse)

    def parse(self, response):
        restaurant_info_item = RestaurantInfoItem()
        foodler_base_url = "https://www.foodler.com/"
        scraped_restaurant_links = set()
        for i in range(len(response.css("a.title::text").extract())):
            href = response.css("a.title::attr(href)").extract()[i][1:]
            insert_index = href.find('/')
            menu_link = (foodler_base_url + href[:insert_index] + "/menu" + href[insert_index:])
            menu_link = menu_link[:menu_link.find(';')]
            if "openChain" in menu_link:
                continue
            if "bb" in menu_link:
                menu_link = menu_link[:-3]
            if menu_link not in scraped_restaurant_links:
                restaurant_name = response.css("a.title::text").extract()[i]
                # zipcode = response.url[len(foodler_base_url):]
                restaurant_info_item["name"] = restaurant_name
                restaurant_info_item['provider'] = self.provider

                scraped_restaurant_links.add(menu_link)
                restaurant_info_item["link"] = menu_link
                # address_link = (foodler_base_url + href[:insert_index] + "/about" + href[insert_index:])
                request = scrapy.Request(menu_link, callback=self.parse_menu, meta={"name": restaurant_name})
                # This line sends the current item into the response as well so we can continue adding to it
                request.meta['item'] = restaurant_info_item
                yield request
                yield restaurant_info_item

    def parse_menu(self, response):
        """Parses each menu item within the menu"""
        name = response.meta['name']
        menu_item = MenuItem()
        soup = BeautifulSoup(response.body, "html.parser")
        headers = soup.find_all("div", {"class": "menuItems"})
        num_headers = len(headers)
        for header_index in range(num_headers):
            # header = headers[header_index].find("h2").get_text()
            menu_items_num = self.get_menu_items_num(header_index, headers)
            for menu_item_index in range(menu_items_num):
                menu_item['name'] = self.get_menu_item_name(header_index, menu_item_index, headers)
                price = self.get_menu_item_price(header_index, menu_item_index, headers)
                menu_item['price'] = price
                menu_item['additional'] = {}
                item_id = self.get_menu_item_id(header_index, menu_item_index, headers)
                additional_info_url = self.get_additional_info_url(item_id)
                additional_info_request = scrapy.Request(url=additional_info_url,
                                                         callback=self.parse_additional_info,
                                                         meta={"price": price, "restaurant_name": name})
                yield additional_info_request

    def parse_additional_info(self, response):
        """This functions parses the additional add-ons for each menu_item"""
        full_menu_item = MenuItem()
        additional_data = json.loads(response.body)
        item_name = additional_data['name']
        item_price = response.meta['price']
        restaurant_name = response.meta['restaurant_name']
        has_different_sizes = self.has_different_sizes(item_price)
        html_source = additional_data['html']
        soup = BeautifulSoup(html_source, "html.parser")
        full_tables = soup.find_all("table", {'class': 'full'})
        size_table = soup.find_all("table", {"class": "size"})
        extra_tables = soup.find_all("table", {"class": "extra"})
        has_extra_prices = self.has_extra_prices(additional_data)
        additional_item_names = []
        names_from_extra_tables = self.get_names_from_extra_tables(extra_tables)
        names_from_full_tables = self.get_names_from_full_tables(full_tables)
        if self.is_not_empty(names_from_full_tables):
            additional_item_names += names_from_full_tables
        if self.is_not_empty(names_from_extra_tables):
            additional_item_names += names_from_extra_tables

        if has_different_sizes:
            sizes = size_table[0].find_all("tr")[1]  # The second tr tag is always the size
            num_sizes = len(sizes.find_all('tr'))
            if has_extra_prices:
                extra_price_lists = re.findall(r'\[\[+[^\;]+', additional_data['ps'])
                extra_price_lists = self.convert_extra_price_lists(extra_price_lists)
                combined_price_lists = self.combine_multiple_sizes_prices(extra_price_lists)
            for size_index in range(num_sizes):
                temp_additional_items = {}
                if additional_item_names:
                    print "Restaurant_name is %s and item_name is %s" % (restaurant_name, item_name)
                    print "length of combinedPriceLists is ", len(combined_price_lists)
                    print "sizeIndex is %s and combinedPriceLists is %s" % (size_index, combined_price_lists)
                    print "additional_item_names is ", additional_item_names
                    temp_additional_items.update({"names": additional_item_names,
                                                  "prices": combined_price_lists[size_index]})
                size_str = sizes.find_all("tr")[size_index].get_text().lstrip().rstrip()
                size_name = size_str[:size_str.find("(")].lstrip().rstrip()
                size_price = size_str[size_str.find("("):]
                size_price = size_price.replace("(", "").replace(")", "")
                full_menu_item['name'] = item_name + " " + size_name
                full_menu_item['price'] = size_price
                full_menu_item['additional'] = temp_additional_items
                full_menu_item['restaurant_id'] = restaurant_name
                full_menu_item['provider'] = self.provider
                yield full_menu_item
        else:
            temp_additional_items = {}
            if has_extra_prices:
                extra_price_lists = re.findall(r'\[\[+[^\;]+', additional_data['ps'])
                extra_price_lists = self.convert_extra_price_lists(extra_price_lists)
                combined_price_lists = self.combine_single_size_prices(extra_price_lists)
            if additional_item_names:
                temp_additional_items.update({"names": additional_item_names, "prices": combined_price_lists})
            full_menu_item['name'] = item_name
            full_menu_item['price'] = item_price
            full_menu_item['additional'] = temp_additional_items
            full_menu_item['restaurant_id'] = restaurant_name
            full_menu_item['provider'] = self.provider
            yield full_menu_item

    def get_menu_items_num(self, header_index, headers):
        """Finds the number of menu items in a menu category/header"""
        return len(headers[header_index].find_all("div", {"class": "mihead"}))

    def get_menu_item_price(self, header_index, menu_item_index, headers):
        """Gets the price of a menu item"""
        menu_item_list = headers[header_index].find_all("div", {"class": "price"})
        price = menu_item_list[menu_item_index].get_text().lstrip().rstrip()
        return price

    def get_menu_item_name(self, header_index, menu_item_index, headers):
        """Gets the menu item name"""
        menu_item_list = headers[header_index].find_all("div", {"class": "mihead"})
        full_string = menu_item_list[menu_item_index].get_text()
        name = full_string[:full_string.find("\n")]
        return name

    def get_menu_item_id(self, header_index, menu_item_index, headers):
        """Gets the menu item id"""
        menu_item_list = headers[header_index]
        menu_item_id = menu_item_list.find_all("div", {"class", "menu-item-cell mi"})[menu_item_index].get("id")
        menu_item_id = menu_item_id[2:]
        # menu_item_name = menu_item_list.find_all("table")[menu_item_index].get_text()
        # print "menu_item_name is %s and menu_item_id is %s" % (menu_item_name, menu_item_id)
        return menu_item_id

    def get_additional_info_url(self, item_id):
        """Get additional info url by combining url with item id"""
        url = "https://www.foodler.com/menu/MenuItemAsync.do?mi=" + item_id + "&s=-1"
        return url

    def convert_to_list(self, string_list):
        """Convert string to list"""
        new_list = ast.literal_eval(string_list)
        return new_list

    def convert_extra_price_lists(self, extra_price_lists):
        """Convert extra price lists for easy parsing"""
        additional_full_list = []
        for additional_list_partition in extra_price_lists:
            additional_list_partition = self.convert_to_list(additional_list_partition)
            additional_list = []
            for additional_list_price in additional_list_partition:
                additional_list.append(additional_list_price)
            additional_full_list.append(additional_list)
        return additional_full_list

    def combine_multiple_sizes_prices(self, additional_full_list):
        """Combine price lists for menu items with multiple sizes"""
        some_list = []
        huge_list = []
        for x in range(len(additional_full_list)):
            for y in range(len(additional_full_list[x])):
                # print "y iterates to %s and x iterates to %s" %(len(additional_full_list[x]), len(additional_full_list))
                # print "y is %s, x is %s" % (y, x)
                # print "aList is ", aList
                some_list += additional_full_list[x][y]
            huge_list.append(some_list)
            some_list = []
        return huge_list

    def combine_single_size_prices(self, price_lists):
        """Combine price lists with only one size"""
        full_list = []
        for price_list in price_lists:
            for price_list_within in price_list:
                for price in price_list_within:
                    full_list.append(price)
        return full_list

    def get_names_from_extra_tables(self, extra_tables):
        """Get addtional item names from table with class name 'full'"""
        additional_full = []
        for extra_table in extra_tables:
            additional_item_names = self.get_additional_item_names(extra_table)
            additional_full += additional_item_names
            # for j in range(len(extra_table.find_all('table'))):
            #     within_table = extra_table.find_all('table')[j]
            #     additionalItemNames = self.getAdditionalItemNames(within_table.find_all('tr'))
            #     additional_full += additionalItemNames

        return additional_full

    def get_additional_item_names(self, item_name_list):
        """Gets the additional item names for menu item"""
        additional_item_names = []
        # for tr_tag in itemNameList:
        #     additional_name = tr_tag.find_all('td')[1].get_text().lstrip().rstrip()
        #     additional_item_names.append(additional_name)
        for label in item_name_list.find_all("label"):
            additional_item_name = label.get_text().lstrip().rstrip()
            additional_item_names.append(additional_item_name)
        return additional_item_names

    def get_names_from_full_tables(self, full_tables):
        """Gets the additional item names from a table with class name 'full' """
        additional_item_names = []
        for full_table in full_tables:
            for tr1 in full_table.find_all("tr"):
                topping_name = tr1.find_all('td')[0].get_text().lstrip().rstrip()
                additional_item_names.append(topping_name)
        return additional_item_names

    def has_different_sizes(self, price):
        """Determines if price is more than one"""
        has_different_sizes_bool = (" " or "-") in price
        return has_different_sizes_bool

    def is_not_empty(self, some_list):
        """Determines if list is empty"""
        if some_list:
            return True
        else:
            return False

    def has_extra_prices(self, additional_data):
        """Detemrines if additional_data contains extra prices"""
        return "ps" in additional_data
