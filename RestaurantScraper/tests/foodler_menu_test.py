import unittest
from RestaurantScraper.spiders import foodler_spider_v3
from tests.responses import fake_response
from scrapy.http import Request
from bs4 import BeautifulSoup

class FoodlerMenuSpiderTest(unittest.TestCase):
    """Tests for foodler_menu_spider"""

    restaurants_url = "https://www.foodler.com/01001"
    menu_url = "https://www.foodler.com/empire-pizza/19319/bb"
    additional_url = "https://www.foodler.com/menu/MenuItemAsync.do?mi=434600321&s=-1"
    def setUp(self):
        self.spider = foodler_spider_v3.FoodlerSpider()

    def _test_item_results(self, results):
        for item in results:
            if isinstance(item, Request):
                continue
            else:
                print item
                self.assertIsNotNone(item['name'])
                self.assertIsNotNone(item['link'])
                self.assertIsNotNone(item['provider'])

    def _test_menu_results(self, results):
        for item in results:
            print item

    def _test_additional_info(self, results):
        for item in results:
            print item

    def test_parse(self):
        """Test the self.parse function in spider"""
        results = list(self.spider.parse(fake_response(self.restaurants_url)))
        self._test_item_results(results)

    def test_parse_menu(self):
        """Test the self.parse_menu() in spider"""
        sample_item = {'link': u'https://www.foodler.com/honey-baked-ham/menu/19419',
                       'name': u'Honey Baked Ham',
                       'provider': 'foodler'}
        results = list(self.spider.parse_menu(fake_response(self.menu_url, sample_item)))
        self._test_menu_results(results)

    def test_parse_additional_info(self):
        """Test the self.parse_additional_info() in spider"""
        sample_meta = {'price': '$5.00', 'restaurant_name': "Honey Baked Ham"}
        results = self.spider.parse_additional_info(fake_response(self.additional_url, sample_meta))
        self._test_additional_info(results)

    def test_get_additional_url(self):
        """Tests the self.get_additional_url() in spider"""
        item_id = "434600321"
        url = self.spider.get_additional_info_url(item_id)
        self.assertEqual(self.additional_url, url)

    def test_menu_item_num_is_not_zero(self):
        """Tests if menu_item_num is not 0"""
        soup = BeautifulSoup(fake_response(self.menu_url))
        headers = soup.find_all("div", {"class": "menuItems"})
        num_headers = len(headers)
        for header_index in range(num_headers):
            test_num = self.spider.get_menu_items_num(header_index, headers)
            self.assertGreater(test_num, 0)
    def test_menu_item_name_has_no_newline(self):
        """Tests that the name does not contain new lines """
        string = "test_string"
        string = self.spider.get_menu_item_name(header_index, menu_item_index, headers)
        self.assertNotIn(string, "\n")
