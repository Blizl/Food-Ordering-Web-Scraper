import scrapy
import csv
from bs4 import BeautifulSoup
from RestaurantScraper.items import RestaurantInfoItem
from scrapy_splash import SplashRequest


class GrubhubSpider(scrapy.Spider):

    name = 'grubhub'
    start_urls = ['https://grubhub.com']
    visited_urls = {}

    def start_requests(self):
        csv_file = open(("/Users/vliang621/Google Drive/Programming/FeederCode/RestaurantScraper/" +
                         "RestaurantScraper/spiders/cities_in_ma_v3.csv"), 'rb')
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        next(csv_reader)
        urls = []
        wait_for_script = ''' function main(splash)
                            assert(splash:go(splash.args.url))
                            while not splash:select('.menuItem-container') do
                                splash:wait(0.1)
                            end
                            return splash:html()
                            end'''
        for row in csv_reader:
            print row
            if "" in row[0]:
                city = row[0].lower().replace(" ", "_")
            else:
                city = row[0].lower()
            url = ("https://www.grubhub.com/delivery/ma-" + city)
            urls.append(url)
        for url in urls:
            print "Going to start ", url
            yield SplashRequest(url, self.parse, endpoint='execute', args={'lua_source': wait_for_script})

    def parse(self, response):
        soup = BeautifulSoup(response.body, "html.parser")
        wait_for_script = '''function main(splash)
                                assert(splash:go(splash.args.url))
                                while not splash:select('.searchResults-container') do
                                    splash:wait(0.1)
                                end
                                return {html=splash:html(), png=splash:png()}
                              end'''
        try:
            max_pages = soup.find("span", {"ng-bind": "browseVm.totalPages"}).get_text()
            print "Max pages is ", max_pages
            for i in range(int(max_pages)):
                url = response.url + "?pageNum=" + str(i + 1)
                print "Url is  %s" % url
                yield SplashRequest(url, self.parse_main_page, endpoint='execute', args={'lua_source': wait_for_script})
        except Exception as e:
            print "Continuing on"

    def parse_main_page(self, response):
        wait_for_menu = '''function main(splash)
                            local url = splash.args.url
                            assert(splash:go(url))
                            while not splash:select('.menuSection-title') do
                                splash:wait(0.1)
                            end
                            return {
                                html = splash:html(),
                                }
                            end'''
        soup = BeautifulSoup(response.body, "html.parser")
        href_list = soup.find_all("a", {"class": "restaurant-name text-wrap"})
        for i in range(len(href_list)):
            item = RestaurantInfoItem()
            item['link'] = "https://grubhub.com" + href_list[i].get("href")
            city = response.url[36:]
            item['zipcode'] = city[:city.find("?")]
            print "link has been taken as ", item['link']
            item['name'] = href_list[i].get("title")
            try:
                item['menu'] = self.visited_urls[item['link']]
                yield item
            except KeyError:
                request = SplashRequest(item['link'], self.parse_restaurant_page, endpoint='execute',
                                        args={'lua_source': wait_for_menu})
                request.meta['item'] = item

                yield request

    def parse_restaurant_page(self, response):
        item = response.meta['item']
        item['menu'] = []
        name_list = []
        price_list = []
        desc_list = []
        soup = BeautifulSoup(response.body, "html.parser")
        for div in soup.find_all("div", {"class": "menuItem-name s-col-xs s-link"}):
            name_list.append(div.get_text())
        for div in soup.find_all("div", {"class": "menuItem-price s-col-xs-3 text-right"}):
            price_list.append(div.get_text())
        for div in soup.find_all('div', {"class": "menuItem-details s-col-xs-12"}):
            if div.get_text() == "":
                description = "No description"
            else:
                description = div.get_text()
            desc_list.append(description)
        # assert (len(name_list) == len(desc_list))
        # assert (len(name_list) == len(price_list))

        for num in range(len(name_list)):
            item['menu'].append([name_list[num], price_list[num], desc_list[num]])
            print "Appended menu"
        self.visited_urls[item['link']] = item['menu']
        yield item
