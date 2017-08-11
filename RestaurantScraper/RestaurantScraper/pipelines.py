# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
# import csv
# from scrapy.exporters import CsvItemExporter
import pymongo
from scrapy.conf import settings
# from scrapy.exceptions import DropItem
from scrapy.exporters import JsonItemExporter


class RestaurantscraperPipeline(object):

    def open_spider(self, spider):
        if spider.name == "eat24":
            # self.file = open("Eat24_MA_with_menu.csv", 'w+')
            # self.exporter = CsvItemExporter(self.file)
            # self.exporter.start_exporting()
            print "eat24 pipeline"
        elif spider.name == "grubhub":
            # self.file = open("Grubhub_MA_data_with_menu.csv", 'w+')
            # self.exporter = CsvItemExporter(self.file)
            # self.exporter.start_exporting()
            print "grubhub pipeline"
        elif spider.name == "foodler_menu_spider":
            self.file = open("foodler_menu_spider.json", "w+")
            self.exporter = JsonItemExporter(self.file)
            self.exporter.start_exporting()
            print "foodler pipeline"
        elif spider.name == "grubhub_v2":
            # self.file = open("grubhub_v2.json", "w+")

            print "starting grubhub_v2"

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()
        print "closing spider"

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item

    '''def __init__(self):
        connection = pymongo.MongoClient(
            settings['MONGODB_SERVER'],
            settings['MONGODB_PORT']
        )
        db = connection[settings['MONGODB_DB']]
        self.collection = db[settings['MONGODB_COLLECTION']]

    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Missing {0}!".format(data))
        if valid:
            self.collection.insert(dict(item))
            # log.msg("Restaurant added to MongoDB database!",
            #         level=log.DEBUG, spider=spider)
            print "Added to MongoDb database"
        return item'''
