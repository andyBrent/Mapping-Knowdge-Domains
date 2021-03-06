# -*- coding: utf-8 -*-
# 得到网页内容
import requests
import io
import sys
import re
from bs4 import BeautifulSoup
import urllib.parse
import urllib.request
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')

class HtmlDownloader(object):

    def __init__(self):
        self.count = 0

    def download(self, url):
        if url is None:
            return
        headers = {'Accept': '*/*',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Cache-Control': 'max-age=0',
                   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
                   'Connection': 'keep-alive',
                   'Referer': 'http://www.baidu.com/'
                   }
        # req = requests.get(url,headers=headers)
        # response = None
        try:
            # 超时则会报错
            response = requests.get(url,headers=headers,timeout=5)
        except:
            self.count += 1
            if self.count > 5:
                print("连续五次超时中断")
                return -1
            return -2
        else:
            self.count = 0
        if response == None or response.status_code != 200:
            return None
        #content返回byte
        return response.content.decode('utf-8')

class HtmlParser(object):

    def parse(self, page_url, html_doc):

        if page_url is None or html_doc is None:
            return
        soup = BeautifulSoup(html_doc, 'html.parser')
        new_urls = self._get_new_urls(page_url, soup)
        new_data = self._get_new_data(page_url, soup)
        return new_urls, new_data

    def _get_new_urls(self, page_url, soup):
        new_urls = set()
        pat = re.compile(r"/item/\S*")  # \S表示非空白就匹配，\s表示空白就匹配
        # 将正则表达式的字符串形式编译成正则表达式对象
        # 百度百科的网址格式  https://baike.baidu.com/item/华为技术有限公司
        # 相当于用正则表达式把网页中a标签中，href匹配得了/item/的都返回（注意：返回的是a标签中包含的所有东西）
        links = soup.find_all('a', href=pat)
        for link in links:
            new_url = link['href']
            # 将一个 page_URL 和new_URL 连接成代表绝对地址的 URL。
            new_full_url = urllib.parse.urljoin(page_url, new_url)
            new_urls.add(new_full_url)
        return new_urls

    def _get_new_data(self, page_url, soup):
        try:
            # 得到通用数据
            new_data = {}
            # 网页全部代码
            new_data['all_data'] = soup
            # 网页url
            new_data['url'] = page_url
            # 标题
            title_node1 = soup.find('dd', class_='lemmaWgt-lemmaTitle-title').find('h1')
            new_data['title'] = title_node1.get_text()
            # 概述
            summary_node = soup.find('div', class_='lemma-summary')
            new_data['summary'] = summary_node.get_text()
            # 点赞数
            vote_count = soup.find('span', class_='vote-count')
            new_data['vote'] = vote_count.get_text()
            # 转发数
            share_count = soup.find('span', class_='share-count')
            new_data['share'] = share_count.get_text()
            # 浏览次数
            views_count = soup.find('dl', class_='lemma-statistics').find('dd', class_='split-line').find('li').find(
                'span')
            new_data['views_count'] = views_count.get_text()

            # 编辑次数
            edit_count = soup.find('dl', class_='lemma-statistics').find('dd', class_='split-line').find('li')
            new_data['edit_count'] = edit_count.get_text()
        except Exception as e:
            print("Web Content doesn't exist")
            return None

        # 多义:不一定每个词条都用,需要筛选后再查
        polysemant = soup.find('ul', class_='polysemantList-wrapper')
        if polysemant == None:
            new_data['polysemant'] = 'null'
        else:
            polysemant = soup.find('ul', class_='polysemantList-wrapper').find_all('li')
            i = 0
            data_list=[]
            for element in polysemant:
                element.get_text()
                data_list.append(element)
                i += 1
            new_data['polysemant'] =data_list

        # 副标题:不一定每个词条都有,需要筛选后再查
        title_node2 = soup.find('dd', class_='lemmaWgt-lemmaTitle-title').find('h2')
        new_data['by_title'] = 'null' if title_node2 == None else title_node2.get_text()

        # 同义词:不一定每个词条都用,需要筛选后再查
        synonym_node = soup.find('span', class_="viewTip-fromTitle")
        new_data['synonym'] = 'null' if synonym_node == None else synonym_node.get_text()

        # 属性值:不一定每个词条都用,需要筛选后再查
        basic_name = soup.find('div', class_='basic-info').find_all('dt')
        basic_value = soup.find('div', class_='basic-info').find_all('dd')
        if basic_value != None:
            i = 0
            for element in basic_name:
                key = element.get_text()
                value = basic_value[i].get_text()
                new_data[key] = value
                i = i + 1

        # 具体内容:不一定每个词条都用,需要筛选后再查？？？

        detail_title = soup.find_all('div', class_='para-title')
        detail_body = soup.find_all('div', class_='para')
        if detail_title != None:
            for element in detail_body:
                new_data['detail'] = new_data['detail'] + '|' + element.get_text()
        else:
            for element in detail_title:
                new_data['detail'] = new_data['detail'] + '|' + element.get_text()
            for element in detail_body:
                new_data['detail'] = new_data['detail'] + '|' + element.get_text()

        # 同组类超链?
        relation_table = soup.find('div', class_='rs-container-foot')

        # 参考资料：不一定每个词条都有，需要筛选有的再查
        lemma_reference = soup.find('dl', class_='lemma-reference').find_all('li')
        if lemma_reference == None:
            new_data['lemma_reference'] = 'null'
        else:
            i = 0
            for element in lemma_reference:
                new_data['lemma_reference'][i] = element.get_text()
                i = i + 1

        # 词条标签：不一定每个词条都有，需要筛选有的再查
        tag_node = soup.find('dd', id="open-tag-item")
        if tag_node == None:
            new_data['tag'] = 'null'
        else:
            open_tag = soup.find('dd', id="open-tag-item").find_all('span')
            i = 0
            for element in open_tag:
                new_data['tag'][i] = element.get_text()
                i = i + 1

        # 在当前词条网页中找到/item/后面的那个数字
        Lemmaid_div = soup.find('div', class_='lemmaWgt-promotion-rightPreciseAd')
        Lemmaid = re.findall('data-lemmaid="(.*)" ', str(Lemmaid_div))
        # 得到Lemmaid(百科网址/item/后面的数字）给提取以及相关信息
        new_data['related_Information'] = self._get_zhixinmap_data(Lemmaid[0])
        if (new_data['related_Information'] == -1):
            return -1

        # 得到点赞数和转发数
        new_data['shareCount'], new_data['likeCount'] = self._get_sharecounter_data(Lemmaid[0])
        if (new_data['shareCount'] == -1):
            return -1

        return new_data

    # ？？？但是这个网站什么都没有
    def _get_zhixinmap_data(self, uuid):
        zhixinmap_url = 'https://baike.baidu.com/wikiui/api/zhixinmap?lemmaId=' + str(uuid)

        try:
            req = urllib.request.Request(zhixinmap_url, None)
            response = urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            # 如果爬取超时了，返回状态1
            return -1
        if response.getcode() != 200:
            # 如果爬取错误返回状态None
            return 'null'

        html = response.read()
        return_items = []
        datas = json.loads(html)  # json.loads()用于将str类型的数据转成dict。
        if (type(datas) != list):
            # 如果爬取到false返回状态None
            return 'null'
        for data in datas:

            return_item = {}

            return_item['tipTitle'] = data['tipTitle']
            subdatas = data['data']

            return_datas = []

            for subdata in subdatas:
                return_data = {}
                return_data['url'] = subdata['url']
                return_data['title'] = subdata['title']
                return_datas += [return_data]

            return_item['data'] = return_datas

            return_items += [return_item]
        return json.dumps(return_items)

    #得到点赞数和转发数
    def _get_sharecounter_data(self, uuid):
        sharecounter_url = 'https://baike.baidu.com/api/wikiui/sharecounter?lemmaId=' + str(uuid)

        try:
            req = urllib.request.Request(sharecounter_url, None)
            response = urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            # 超时的话返回状态-1，-1
            return -1, -1
        if response.getcode() != 200:
            # 读取错误的返回状态-2，-2
            return 'null', 'null'

        html = response.read().decode('utf-8')
        shareCount = re.findall('shareCount":"(.*?)"', html)
        likeCount = re.findall('likeCount":"(.*?)"', html)
        shareCount = shareCount[0] if len(shareCount) == 1 else 'null'
        likeCount = likeCount[0] if len(likeCount) == 1 else 'null'
        return shareCount, likeCount

url='https://baike.baidu.com/item/猫/22261'

#发起请求
dataobj=HtmlDownloader()
data=HtmlDownloader.download(dataobj,url=url)
#解析数据
new_urls, new_data=HtmlParser().parse(page_url=url,html_doc=data)
print(len(new_urls))

with open('test.html','w',encoding='utf-8')as file:
    file.write(str(new_data))