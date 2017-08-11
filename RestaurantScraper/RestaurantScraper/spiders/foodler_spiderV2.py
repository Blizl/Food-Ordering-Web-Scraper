import scrapy
from scrapy_splash import SplashRequest
from bs4 import BeautifulSoup as bs
from RestaurantScraper.items import RestaurantInfoItem
import json


'''This file accurately scrapes the data as well as additional items from a menu
    TODO: 1. Looks through 3 different htmls, adding items to dictionary that may have been added before, choose to
             ignore values added from before'''


class FoodlerV2Spider(scrapy.Spider):
    name = "foodler_splash"

    start_urls = ["https://www.foodler.com/deliworks/menu/21925"]

    def start_requests(self):
        click_script = '''
function main(splash)
            local click_menuItems = splash:jsfunc([[
            function () {
                var body = document.body;
                var menuItems = body.getElementsByClassName('mihead');
                for (var i = 0; i < menuItems.length; i++) {
                    menuItems[i].click();
                         }
                }
                    ]])

            local find_max_num_of_radios = splash:jsfunc([[
                function(){
                    var body = document.body;
                    var max = 0;
                    var sizesClass = body.querySelectorAll('.size');
                    for (var i = 0; i < sizesClass.length; i++){
                        if (sizesClass[i].querySelectorAll("input[onClick][type='radio']").length > max){
                            max = sizesClass[i].querySelectorAll("input[onClick][type='radio']").length;
                        }
                    }
                    return max;
                }
            ]])


            local click_all_radio_index = splash:jsfunc([[
                function(radio_index){
                    var body = document.body;
                    var sizesClass = body.querySelectorAll('.size');
                    for (var i = 0; i < sizesClass.length; i++){
                        if (sizesClass[i].querySelectorAll("input[onClick][type='radio']").length > radio_index +1 ){
                            sizesClass[i].querySelectorAll("input[onClick][type='radio']")[radio_index].click();
                        }
                    }
                }
            ]])
            local get_last_menuItem = splash:jsfunc([[
                function(){
                    var body = document.body;
                    var miOpts = body.getElementsByClassName('miopt');
                    return miOpts[miOpts.length -1 ].id;
                    }
                ]])
            htmls = {}
            local url = splash.args.url
            splash:go(url)
            click_menuItems()
            splash:set_viewport_full()
            last_item = "#" .. get_last_menuItem() .. " .btn"
            while not splash:select(last_item) do
                splash:wait(0.1)
            end
            table.insert(htmls, splash:html())
            for i=1, find_max_num_of_radios() -1 do
                click_all_radio_index(i)
                table.insert(htmls, splash:html())
            end
            return htmls
        end'''
        url = "https://www.foodler.com/deliworks/menu/21925"
        yield SplashRequest(url, callback=self.parse_menu, endpoint='execute', args={'lua_source': click_script})

    def parse_menu(self, response):
        '''First html corresponds to all small sizes, second html is all large sizes, and after that is others'''
        item = RestaurantInfoItem()
        item['menu'] = {}
        num_of_htmls = len(response.data.keys())
        for html_num in range(num_of_htmls):
            html = response.data[str(html_num + 1)]
            soup = bs(html, "html.parser")
            for menuItem in soup.find_all('div', {'class': 'menuItems'}):
                header = menuItem.find("a").find("h2").get_text()
                for table in menuItem.find_all("table"):
                    names = table.find_all("tr")[0]
                    name = names.find("td", {"class": "mihead"})
                    try:
                        name = name.get_text()
                        item_name = name[:name.find("\n")].lstrip().rstrip()
                        # Full table represents the toppings
                        full_tables = table.find_all("table", {'class': 'full'})
                        extra_tables = table.find_all("table", {'class': 'extra'})
                        additional_items = {}
                        for full_table in full_tables:
                            for tr1 in full_table.find_all("tr"):
                                # print "Label"
                                topping_name = tr1.find_all('td')[0].get_text().lstrip().rstrip()
                                topping_price = tr1.find_all('td')[1].get_text()
                                additional_items.update({topping_name: topping_price})
                        for extra_table in extra_tables:
                            for within_table in extra_table.find_all('table'):
                                for tr2 in within_table.find_all('tr'):
                                    additional_name = tr2.find_all('td')[1].get_text().lstrip().rstrip()
                                    additional_price = tr2.find_all('td')[2].get_text()
                                    # print "addditional name and price is", (additional_name, additional_price)
                                    additional_items.update({additional_name: additional_price})

                        descs = table.find_all("tr")[1]
                        desc = descs.find("td", {"class": "midesc"})
                        size_table = desc.find_all("table", {"class": "size"})
                        if size_table:
                            row = size_table[0].find_all("tr")[1]  # The second tr tag is always the size
                            num_radios = len(row.find_all('tr'))
                            if num_radios < 3 and html_num > 1:
                                continue
                            else:
                                print "html_num is ", html_num
                                size_str = row.find_all("tr")[html_num].get_text().lstrip().rstrip()
                                size_name = size_str[:size_str.find("(")].lstrip().rstrip()
                                size_price = size_str[size_str.find("("):]
                                size_price = size_price.replace("(", "").replace(")", "")
                                # names = re.findall(r'[^$.\d)(\s:]\w+', size_str.replace("\n", ""))
                                # prices = re.findall(r'(?<=\(\$)[^)]+', size_str.replace("\n", ""))
                                item['menu'].update({item_name + " " + size_name:
                                                    {"price": size_price,
                                                     "additional": additional_items}})

                        else:
                            item_price = names.find("td", {"class": "price"}).get_text().lstrip().rstrip()
                            item['menu'].update({item_name: item_price})
                    except AttributeError:
                        continue
        # with open("test.json", "w+") as json_file:
        #     json.dump(item['menu'], json_file)
