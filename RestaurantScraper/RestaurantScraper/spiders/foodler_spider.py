import scrapy
from RestaurantScraper.items import RestaurantInfoItem
import csv

"""TODO: Bug List:
    1. Some restaurant names/zipcodes are missing but menu is being scrape
    2. When scraped, some items have two prices, one for small, one for large, create a seperate entry for each instead
    of one combined item"""


class FoodlerSpider(scrapy.Spider):
    name = "foodler"

    start_urls = [
        "https://www.foodler.com/"
    ]
    visited_urls = {}
    """start_requests() set up the urls that should be looped through"""
    def start_requests(self):
        """TODO: in the future, need to extend the zipcodes to all of USA"""
        first_state_zipcode = 1001
        last_state_zipcode = 2791
        foodler_base_url = "https://www.foodler.com/"
        for zipcode in range(first_state_zipcode, last_state_zipcode):
            if len(str(zipcode)) == 4:
                zipcode_str = "0" + str(zipcode)
            else:
                zipcode_str = str(zipcode)
            print "zipcode is %s" % zipcode_str
            yield scrapy.Request(foodler_base_url + zipcode_str, callback=self.parse)

    """parse() parses the site to get name, link, zipcode, menu(name, price, desciption)"""
    def parse(self, response):
        foodler_base_url = "https://www.foodler.com/"
        for i in range(len(response.css("a.title::text").extract())):
            scraped_restaurants = []

            restaurant_link = foodler_base_url + response.css("a.title::attr(href)").extract()[i][1:]
            """Ensures same restaurant is not added more than once"""
            if restaurant_link not in scraped_restaurants:
                href = response.css("a.title::attr(href)").extract()[i][1:]  # Find restaurant link Ex: mjs/01929
                restaurant_name = response.css("a.title::text").extract()[i]
                restaurant_link = foodler_base_url + href
                # Strip jession id from link
                restaurant_link = restaurant_link[:restaurant_link.find(";")]
                # Gets rid of the javascript link for when it is a chain restaurant with different location
                if "openChain" in restaurant_link:
                    continue
                zipcode = response.url[len(foodler_base_url):]
                # Add the data scrpaed into the RestaurantInfoItem object
                item = RestaurantInfoItem()
                item["name"] = restaurant_name
                item['provider'] = "foodler"

                scraped_restaurants.append(restaurant_link)

                insert_index = href.find('/')
                menu_link = (foodler_base_url + href[:insert_index] + "/menu" + href[insert_index:])
                if menu_link in self.visited_urls:
                    continue
                item["link"] = menu_link
                address_link = (foodler_base_url + href[:insert_index] + "/about" + href[insert_index:])

                request = scrapy.Request(address_link, callback=self.parse_address)
                # This line sends the current item into the response as well so we can continue adding to it
                request.meta['item'] = item
                yield request

    def parse_address(self, response):
        item = response.meta['item']
        item['address'] = ''.join(response.css("div.aboutRestaurant #address::text").extract()).replace("\n", "")
        try:
            item['menu'] = self.visited_urls[item['link']]
            yield item
        except KeyError:
            request = scrapy.Request(item['link'], callback=self.parse_menu)
            # This line sends the current item into the response as well so we can continue adding to it
            request.meta['item'] = item
            yield request

    """parse_menu() will parse each restaurant to get the menu(name, price, description)"""
    def parse_menu(self, response):
        item = response.meta['item']
        item['menu'] = {}
        for x in range(len(response.css('div.menuItems').css("a.menuItemsHeader h2::text"))):
            header = response.css('div.menuItems')[x].css("a.menuItemsHeader h2::text").extract_first()
            item['menu'].update({header: {}})
            for y in range(len(response.css('div.menuItems')[x].css('td.price').css("div ::text"))):
                item_price = response.css('div.menuItems')[x].css('td.price')[y].css("div ::text").extract()  # size 29
                item_name = response.css('div.menuItems')[x].css("td.mihead")[y].css("::text").extract_first().lstrip().rstrip() # max 29
                item_description = response.css('div.menuItems')[x].css("td.mihead")[y].css("p::text").extract_first()
                if item_description == "":
                    item_description = "No description"
                item['menu'][header].update({item_name: {"price": item_price, "description": item_description}})

        self.visited_urls[item['link']] = item['menu']

        yield item
