# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time
import re
import pymongo
from weibosearch.items import WeiboItem

'''
对从spider中得到的item进行数据清理，改写数据
'''

class WeiboPipeline(object):

    # 三种时间类型的转化
    def parse_time(self,datetime):
        if re.match('\d+月\d+日',datetime):
           datetime = time.strftime('%Y年',time.localtime())+datetime

        if re.match('\d+分钟前',datetime):
            minute = re.match('(\d+)',datetime).group(1)
            datetime = time.strftime('%Y年%m月%d日',time.localtime(time.time()-float(minute)))

        if re.match('今天.*',datetime):
            # 匹配到字尾的话需要使用（.*）
            datetime = re.match('今天(.*)',datetime).group(1)
            datetime = time.strftime('%Y年%m月%d日',time.localtime())+' '+datetime

        return datetime


    def process_item(self, item, spider):
        if isinstance(item,WeiboItem):
            if item.get('content'):
                # 去除左边的冒号，并清除左右两端的空格
                item['content'] = item['content'].lstrip(':').strip()
            if item.get('post_at'):
                item['posted_at'] = item['posted_at'].strip()
                # 将发布时间中包含类似 ：“今天” 的这样的数据进行改写
                item['posted_at'] = self.parse_time(item['posted_at'])


class MongoPipeline():

    def __init__(self,mongo_uri,mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    # 通过crawler这个变量拿到settings中的mongo的配置
    @classmethod
    def from_crawler(cls,crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI'),
            mongo_db = crawler.settings.get('MONGO_DB')
        )

    # 在spider开启的时候，默认开启的方法
    def open_spider(self,spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    # 在spider结束的时候做一些收尾的操作
    def close_spider(self,spider):
        self.client.close()

    def process_item(self,item,spider):
        # 第三个参数：true：查询到数据进行更新，查询不到进行插入
        # 这样可以做到对数据进行去重
        self.db[item.table_name].update({'id':item.get('id')},{'$set':dict(item)},True)
        return item

