# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json
import logging
import requests
from scrapy.exceptions import IgnoreRequest

'''
    从cookies池中获取cookie，改写Request请求中的cookie
    在settings中启用CookiesMiddleware
'''
class CookiesMiddleware():
    # 日志输出
    def __init__(self,cookies_pool_url):
        self.logger = logging.getLogger(__name__)
        self.cookies_pool_url = cookies_pool_url


    def _get_random_cookies(self):
        try:
            response = requests.get(self.cookies_pool_url)
            if response.status_code == 200:
                return json.loads(response.text)
        except ConnectionError:
            return None

    # 从settings中获取cookie池的连接
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            cookies_pool_url = crawler.settings.get('COOKIES_POOL_URL')
        )

    # 设置Request请求中的cookies
    def process_request(self,request,spider):
        cookies = self._get_random_cookies()
        if cookies:
            request.cookies = cookies
            self.logger.debug("Using Cookies" + json.dumps(cookies))
        else:
            self.logger.debug("No Valid Cookies")

    # 微博的反爬虫比较厉害，可能跳转到封号的页面去
    # 那么我们需要在这个中间件里面另外的加一些判断
    def process_response(self,request,response,spider):
        if response.status in [300,301,302,303]:
            try:
                # 重定向的url
                redirect_url = response.headers['location']

                if 'passport' in redirect_url:
                    self.logger.warning('Need Login, Updating Cookies')
                elif 'weibo.cn/security' in redirect_url:
                    # 封号界面
                    self.logger.warning('Account is Locked')
                # 重新获得cookies
                request.cookies = self._get_random_cookies()
                # 重新加入到调度队列里面
                return request
            except:
                raise IgnoreRequest
        elif response.status in [414]:
            # 代表url请求过长
            return request
        else :
            response