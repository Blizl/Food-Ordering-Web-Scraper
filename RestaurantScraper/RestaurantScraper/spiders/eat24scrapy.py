import scrapy
import csv
from RestaurantScraper.items import Eat24InfoItem

'''This spider gets the menu information and outputs a CSV file with menu and the link, another script is
needed to get name, zipcode, link, and menu'''


class Eat24Spider(scrapy.Spider):
    name = "eat24"
    allowed_domains = ["eat24.com"]
    start_urls = []
    url_set = set()

    def start_requests(self):
        read_file = open("Eat24_MA_V2.1.csv", "r")
        reader = csv.reader(read_file)
        for row in reader:
            self.url_set.add(row[3])
        read_file.seek(0)  # Return to the top of the file
        for row in reader:
            if row[3] in self.url_set:
                url = (row[2] + row[3]).replace("\\", "")
                self.start_urls.append(url)
                self.url_set.remove(row[3])
        read_file.close()
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        name = []
        price = []
        desc = []
        menu = []
        x1 = response.xpath('//*[@id="contents_list"]')

        for i in range(len(x1.css('span[itemprop="price"]::text').extract())):

            name.append(x1.css('a.cpa')[i].css('::text').extract())
            price.append(x1.css('span[itemprop="price"]')[i].css('::text').extract())

            if x1.css('div.item_desc')[i].css("::text") == []:
                desc.append("No Description")
            else:
                desc.append(x1.css('div.item_desc')[i].css("::text").extract())

        for num in range(len(name)):
            menu.append([name[num], price[num], desc[num]])

        string_part = response.url.find("eat24")
        link = response.url[string_part + 15:]
        item = Eat24InfoItem()

        item['link'] = link
        item['menu'] = menu

        yield item
