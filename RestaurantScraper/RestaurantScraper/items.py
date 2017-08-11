# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RestaurantInfoItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    link = scrapy.Field()
    address = scrapy.Field()
    menu = scrapy.Field()
    provider = scrapy.Field()


class Eat24InfoItem(scrapy.Item):
    link = scrapy.Field()
    menu = scrapy.Field()


class MenuItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    additional = scrapy.Field()
    provider = scrapy.Field()
    restaurant_id = scrapy.Field()
    header = scrapy.Field()
    additional_url = scrapy.Field()  # Used for testing only
