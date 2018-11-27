# -*- coding: utf-8 -*-
import re
from scrapy import Spider,FormRequest,Request
from weibosearch.items import WeiboItem


class WeiboSpider(Spider):
    name = 'weibo'
    allowed_domains = ['weibo.com']
    start_url = 'https://weibo.cn/search/mblog'
    max_page = 100

    def start_requests(self):
        keyword = '000001'
        url = '{url}?keyword={keyword}'.format(url=self.start_url,keyword=keyword)
        for page in range(self.max_page+1):
            data = {
                'mp': self.max_page,
                'page':page
            }
        yield FormRequest(url,callback=self.parse_index,formdata=data)

    def parse_index(self, response):
        weibos = response.xpath('//div[@class="c" and contains[@id,"M_"]')

        '''
        判定微博是否是原创，根据对网站的源码分析，发现转发的微博中都含有<span class='cmt'>标签
        '''
        for weibo in weibos:
            is_forward = bool(weibo.xpath('.//@span[class="cmt"]').extract_first())

            if is_forward:
                # contains(.,"原文评论[") .表示当前文本
                detail_url = weibo.xpath('.//@a[contains(.,"原文评论[")]//@href').extract_first()
            else:
                detail_url = weibo.xpath('.//@a[contains(.,"评论[")]//@href').extract_first()

            yield Request(detail_url,callback= self.parse_detail)

    def parse_detail(self, response):
        id = re.search('comment\/(.*?)\?',response.url).group(1)
        url = response.url
        # 使用join将extract中的内容拼接起来
        content =''.join(response.xpath('//div[@id="M_"]//span[@class="ctt"]//text()').extract())
        # 评论数量
        comment_count = response.xpath('//span[@class="pms"]//text()').re_first('评论\[(.*?)\]')
        # 转发数量
        forward_count = response.xpath('//a[contains(.,"转发[")]//text()').re_first('评论\[(.*?)\]')
        # 赞的数量
        like_count = response.xpath('//a[contains(.,"赞[")]//text()').re_first('赞\[(.*?)\]')
        # 发布时间
        posted_at = response.xpath('//div[@id="M_"]//span[@class="ct"]//text()').extract_first(default=None)
        # 发布人
        user = response.xpath('//div[@id="M_"]/div[1]/a/text()').extract_first(default=None)
        # 引入items文件中的WeiboItem
        weibo_item = WeiboItem()
        # 对WeiboItem中的字段进行赋值
        # weibo_item.fields 对item中所有的字段进行循环
        for field in weibo_item.fields:
            try:
                # 利用eval，对Item中的字段进行对台的赋值
                weibo_item[field] = eval(field)
            except NameError:
                self.logger.debug("Filed is Not Defind." + field)

        yield weibo_item
