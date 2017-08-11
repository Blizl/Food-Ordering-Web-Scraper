import os
import requests
from scrapy.http import TextResponse, Request

def fake_response(url, meta=None):
    """Create fake scrapy HTTP response from url"""

    response_with_body = requests.get(url)
    request = Request(url=url, meta=meta)

    response = TextResponse(url=url, request=request, body=response_with_body.content)

    return response
    