# -*- encoding: utf-8 -*-
'''
@File    :   build_kg.py
@Time    :   2024/07/06 21:24:14
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

build Knowledge Graph of SCP objects
'''
import re
import os
from pathlib import Path
from urllib.request import urlopen
import json

from joblib import Parallel, delayed

from scrapy import Selector
import opencc
converter = opencc.OpenCC('t2s')

XPATH_CONTENT = './/div[@id="page-content"]'
LINK_EXCLUDE = set()
LINK_EXCLUDE.add('classification-committee-memo.html')

TAG_UNSAVED = set([
    '组件', '组件后端', '版式', '样版',
    '指导', '文章', '新闻', '资源', '必要', 
    '艺术作品', '作者', '艺术家',
    '工房', '讨论区', '草稿','漫画', 
])
SENTENCE_END = set('。！？')
CSS_REMOVE = [
    'div[style="display: none"]',
    'div[style="display: none;"]',
    'div.code',
    'div.pseudocrumbs',
    'div.adytoc',
    'div#u-credit-view',
    'div.page-rate-widget-box', 
    'div.creditRate', 
    'div.licensebox',
    'div.info-container',
    'div.footer-wikiwalk-nav',
    'div.footnotes-footer',
    'div#breadcrumbs',
    'script',
    'div[class="scp-image-caption show"]',
    'span.fnnum',
    'span.footnoteref',
    'sup.footnoteref',
    'span.fncon',
    'style',
    'div#counter',
]
CSS_FOOTNOTE = [
    'span.footnoteref',
    'sup.footnoteref',
    'span.fncon',
]
XPATHSTR_BLOCK_STARTWITH = [
    '<hr>',
    '<p><strong>',
    '<p><b>',
    '<strong>',
]
XPATHSTR_BLOCK_ENDWITH = [  
    '<div class=',
    '<table',
    # '<blockquote>',
    '<div style=',    
]

QUOTE_START = ('“', '「', '[', '【', '{', '‘', '<', '《', '(', '（', '"')
QUOTE_END = ('”', '」', ']', '】', '}', '’', '>', '》', ')', '）', '"')
DICT_QUOTE = dict([(s, e) for s, e in zip(QUOTE_START, QUOTE_END)])
        

class Page(object):
    def __init__(
        self, 
        html_file: str = None,
        dict_json: dict = None,
    ) -> None:
        assert html_file is not None or dict_json is not None
        if dict_json is not None:
            for k, v in dict_json.items():
                setattr(self, k, v)
        else:
            self.wikidot_address = html_file.split('wikidot.com/')[-1][:-5]
            with open(html_file) as f:
                self.pagedata = Selector(text=f.read())
            self.update_tag()


    def update_tag(self) -> None:
        self.tag = set()
        for i in self.pagedata.xpath('.//div[@class="page-tags"]/span/a'):
            self.tag.add(i.xpath('string(.)').extract_first())


    def update_link(self) -> None:
        self.link: list[str] = []
        all_content = self.pagedata.xpath(XPATH_CONTENT)
        all_content_text = all_content.extract_first()
        # 没有页面内容
        if all_content_text is None:
            return None
        # 移除不属于正文的节点
        for i in CSS_REMOVE:
            for j in all_content.css(i).extract():
                all_content_text = all_content_text.replace(j, '')
        all_link = Selector(text=all_content_text).xpath(XPATH_CONTENT + '/descendant::*/a/@href').extract()[::-1]
        all_link_text = Selector(text=all_content_text).xpath(XPATH_CONTENT + '/descendant::*/a').xpath('string(.)').extract()[::-1]
        for l, t in zip(all_link, all_link_text):
            if l[-5:]=='.html' and l not in LINK_EXCLUDE:
                self.link.append({'link': l[:-5], 'text': t})


    def update_text_block(self) -> None:
        self.text_block: list[str] = []
        # TODO: corner case: scp-6013
        all_content = self.pagedata.xpath(XPATH_CONTENT)

        # raw text of the whole page
        all_content_text = all_content.extract_first()

        # 没有页面内容
        if all_content_text is None:
            return None

        # wrap raw text in <p> flag
        for i in self.pagedata.xpath(XPATH_CONTENT + '/text()').extract():
            i = i.strip()
            if i != '':
                all_content_text = all_content_text.replace(i, f'<p>{i}</p>')    

        # download contents in iframe link, then write them in all_content_text
        # only download when there is too little text extracted
        # downloading from internet will make the parsing procedure obviously slower
        # if len(all_content.xpath('string(.)').extract_first()) < 300:
        #     for i in self.pagedata.xpath(XPATH_CONTENT + '/*/iframe'):
        #         src = i.xpath('@src').extract_first()
        #         try:
        #             content = urlopen(src).read().decode()
        #             # if div#doc exists, page content is always in div#doc
        #             # only 3 scp objects in iframe-div#doc...
        #             if '<div id="doc"' in content:
        #                 print('iframe doc found')
        #                 all_content_text = Selector(text=content).css('div#doc').extract_first()
        #                 break
        #             all_content_text = all_content_text.replace(i.extract(), content)
        #         except Exception:
        #             pass
        #     all_content = Selector(text=all_content_text)

        # print(all_content)
        # 移除不属于应生成文本的节点
        for i in CSS_REMOVE:
            for j in all_content.css(i).extract():
                all_content_text = all_content_text.replace(j, '')

        all_content = Selector(text=all_content_text).xpath('*')
        # print(all_content.xpath('string(.)').extract())
        
        # 将表格中的每一行分别合并成一个字符串，以 '【】' 表示每行的开始和结束
        # 以 '|' 分隔每列, 以 '; ' 分隔每列中的换行
        for i in all_content.css('tr').extract():
            s_list = []
            for j in Selector(text=i).css('th,td'):
                s_list.append(j.xpath('string(.)').extract_first().replace('\n', '; '))
            tr = f'<tr><td>【{"|".join(s_list)}】</td></tr>'
            all_content_text = all_content_text.replace(i, tr)
        

        # raw text of the whole page
        # text = []
        # pattern = r'\s*\n+\s*'
        # for i in all_content.xpath('string(.)').extract():
        #     i = i.strip()
        #     if i != '':
        #         text.append(i)
        # # replace multiple continuous \n with only one \n
        # text = re.sub(pattern, '\n', '\n'.join(text))
        # self.text = text

        # list of blocks, footnote not included
        # TODO：加入注脚文本
        # 自动寻找大部分文本内容（90%）的最低级节点
        min_percentage = 0.90
        len_all_text = len(Selector(text=all_content_text).xpath('*').xpath('string(.)').extract_first())
        min_len = int(len_all_text * min_percentage)
        for i in Selector(text=all_content_text).xpath('/descendant::*')[::-1]:
            # print(i.extract()[:50])
            # print(len(i.xpath('string(.)').extract_first()))
            if len(i.xpath('string(.)').extract_first()) >= min_len:
                # print(i.xpath('string(.)').extract())
                # print(i.xpath('*').xpath('string(.)').extract())
                # TODO: text missing when excecuting i.xpath('*')
                # i.e. scp-cn-1837
                all_content = i.xpath('*')
                break
        # print('len_all_text', len_all_text)
        # print('min_len', len_all_text)
        # print(all_content.xpath('string(.)').extract())
        all_content = all_content.extract()

        # 没有页面内容
        if len(all_content) == 0:
            return None

        # TODO: better extraction of text blocks
        list_block = [all_content[0]]
        block_end = False
        for i in XPATHSTR_BLOCK_ENDWITH:
            if list_block[0].startswith(i):
                block_end = True
                break

        for i in all_content[1:]:
            start_new_block = False
            # start of blocks
            for j in XPATHSTR_BLOCK_STARTWITH + XPATHSTR_BLOCK_ENDWITH:
                if i.startswith(j):
                    # skip text in a image block
                    if i.startswith('<div class="scp-image-block block-right"'):
                        start_new_block = True
                        break
                    else:
                        list_block.append(i)
                        start_new_block = True
                        block_end = j in XPATHSTR_BLOCK_ENDWITH
                        break
            if not start_new_block:
                # start new block
                if block_end:
                    list_block.append(i)
                # concat old block
                else:
                    list_block[-1] += i
        
        self.text_block: list[str] = []
        pattern = r'\s*\n+\s*'
        for i in list_block:
            i = Selector(text=i).xpath('string(.)').extract_first().strip()
            if i != '':
                i = re.sub(pattern, '\n', i)
                # i = converter.convert(i)
                self.text_block.append(i)


    def get_dict(self) -> dict:
        d = vars(self)
        d.pop('pagedata', None)
        # d.pop('text_block', None)
        d['tag'] = list(d['tag'])
        return d


def scan_html_single(
    dir_wikidot: str,
    path: str,
    tag: set[str],
) -> list[str] | None:
    i = path
    if not i.endswith('.html'):
        return None
    if len(tag) > 0:
        page = Page(dir_wikidot+i)
        if not tag.issubset(page.tag):
            return None
    list_html_object = [dir_wikidot + i]
    dir_scp = Path(dir_wikidot + i[:-5])
    if dir_scp.exists:
        for root, dirs, files in os.walk(dir_scp):
            for name in files:
                file_path = os.path.join(root, name)
                if file_path.endswith('.html'):
                    list_html_object.append(file_path)
    return list_html_object


def scan_html(
    tag: list[str] = ['scp'],
    dir_wikidot: str = '../SCP-CN/scp-wiki-cn.wikidot.com/',
    n_limit: int = None,
) -> list[list[str]]:
    print('Scanning HTML')
    if tag is not None:
        tag = set(tag)
    args = [(dir_wikidot, i, tag) for i in os.listdir(dir_wikidot)]
    pool = Parallel(-1)
    list_html = []
    for j in pool(delayed(scan_html_single)(*i) for i in args):
        if j is not None:
            list_html.append(j)
        if n_limit is not None and len(list_html) > n_limit:
            break
    print('HTML Scanned')
    return list_html


def get_page_dict(list_html: list[str]) -> list[dict]:
    list_dict = []
    for i in list_html:
        page = Page(i)
        page.update_link()
        page.update_text_block()
        list_dict.append(page.get_dict())
    return list_dict


def save_page(
    list_html: list[list[str]],
    page_json: str = '../data/page.scp.json',
) -> list[dict]:
    print('Parsing all Pages')
    pool = Parallel(-1)
    result = [i for i in pool(delayed(get_page_dict)(j) for j in list_html)]
    with open(page_json, 'w') as f:
        s = json.dumps(result, ensure_ascii=False, indent=2)
        s = converter.convert(s)
        f.write(s)
        # json.dump(result, f, ensure_ascii=False, indent=2)
    print('All Page objects Parsed and Saved')   
    return result 


def get_page_from_json(
    page_json: str = '../data/page.scp.json',
    tag: str = None,
) -> list[list[Page]]:
    with open(page_json) as f:
        list_page_all = json.load(f)
    list_page = []
    for i in list_page_all:
        if tag is None:
            list_page.append([Page(dict_json=j) for j in i])
        else:
            if tag in i[0]['tag']:
                list_page.append([Page(dict_json=j) for j in i])
    return list_page


if __name__ == '__main__':
    address = 'scp-cn-1837'
    html_file = f'../SCP-CN/scp-wiki-cn.wikidot.com/{address}.html'


    list_html = scan_html(n_limit=None)
    result = save_page(list_html)

    # page = Page(html_file)
    # page.update_text_block()
    # text_block = page.text_block
    # for i in text_block:
    #     print(i)

    # with open(html_file) as f:
    #     pagedata = Selector(text=f.read())
            
    # all_content = pagedata.xpath(XPATH_CONTENT)
    # all_content_text = all_content.extract_first()
    # for i in pagedata.xpath(XPATH_CONTENT + '/text()').extract():
    #     i = i.strip()
    #     if i != '':
    #         all_content_text = all_content_text.replace(i, f'<p>{i}</p>')
    # all_content = pagedata.xpath(XPATH_CONTENT)

    # # raw text of the whole page
    # all_content_text = all_content.extract_first()
