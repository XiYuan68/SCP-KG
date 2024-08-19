# -*- encoding: utf-8 -*-
'''
@File    :   build_kg.py
@Time    :   2024/07/06 21:24:14
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

parse pages of wikidot
'''
import re
import os
from pathlib import Path
from urllib.request import urlopen
import json
import logging

from joblib import Parallel, delayed
from scrapy import Selector
from scrapy.selector import SelectorList
import opencc
converter = opencc.OpenCC('t2s')
import cssutils
# import timeout_decorator

from utilities import DIR_WIKIDOT, strip_address, xstr, xhref


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
    # 'div#breadcrumbs',
    'script',
    'div.scp-image-block',
    'div.scp-image-caption',
    'div.image-box',
    'span.fnnum',
    'span.footnoteref',
    'sup.footnoteref',
    'span.fncon',
    'span.lang-tr',
    'style',
    'div#counter',
    # TODO: include text with line-through
    'span[style="text-decoration: line-through;"]',
    'span[style="text-decoration: line-through"]',
]
CSS_FOOTNOTE = [
    'span.footnoteref',
    'sup.footnoteref',
    'span.fncon',
]
# this node starts a block, but not neccessarily close the block
BLOCK_START = [
    '<hr>',
    '<p><strong>',
    '<p><b>',
    '<strong>',
    '<h1>',
    '<h2>',
    '<h3>',
    '<h4>',
]
# this node is a complete block
BLOCK_CLOSE = [  
    '<div class=',
    '<table',
    '<blockquote>',
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
            self.address = strip_address(html_file)
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
        # class of div that has css property border
        # used to determind blocks of text
        # TODO: slow for joblib parallelization
        style_valid = parse_style_border(self.pagedata)
        self.class_stop = set([i[1:] for i in style_valid if i.startswith('.')])
        # self.class_stop = set()
        self.class_stop.add('blockquote')

        # TODO: corner case: scp-6013
        all_content = self.pagedata.xpath(XPATH_CONTENT)
        all_content = unfold_colmod(all_content)

        # raw text of the whole page
        all_content_text = all_content.extract_first()

        # 没有页面内容
        if all_content_text is None:
            return None

        # TODO: better replacement; scp-cn-1837
        # wrap raw text in <p> flag
        for i in self.pagedata.xpath(XPATH_CONTENT + '/text()').extract():
            i = i.strip()
            if i != '' and all_content_text.count(i)==1:
                all_content_text = all_content_text.replace(i, f'<p>{i}</p>')
        # print(all_content_text)

        # 下载iframe标签所指向的html文件
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
        
        # 将表格中的每一行分别合并成一个字符串，以 '【】' 表示每行的开始和结束
        # 以 '|' 分隔每列, 以 '; ' 分隔每列中的换行
        for i in all_content.css('tr').extract():
            s_list = []
            for j in Selector(text=i).css('th,td'):
                s_list.append(j.xpath('string(.)').extract_first().replace('\n', '; '))
            tr = f'<tr><td>【{"|".join(s_list)}】</td></tr>'
            all_content_text = all_content_text.replace(i, tr)
        
        # 递归展开所有div元素，直到div元素的css-style具有border特性
        # 效果：一个带边框效果的div将被视为一个block
        all_content = Selector(text=all_content_text).css('div#page-content').xpath('*')
        # list_unfolded中一个元素为一个block（或一个block的一部分）
        list_unfolded = unfold(all_content, self.class_stop).extract()
        # for i in list_unfolded:
        #     print(i)
        #     print('*'*50)
        # 没有页面内容
        if len(list_unfolded) == 0:
            return None

        # 按标签区分block
        last_block_finished = True
        list_block = []
        for i in list_unfolded:
            start = False
            for j in BLOCK_START:
                if i.startswith(j):
                    start = True
                    break
            close = False
            for j in BLOCK_CLOSE:
                if i.startswith(j):
                    close = True
                    break
            if close or start:
                list_block.append(i)
            else:
                if last_block_finished:
                    list_block.append(i)
                else:
                    list_block[-1] += '\n'+i
            last_block_finished = close
        
        self.text_block: list[str] = []
        pattern = r'\s*\n+\s*'
        pattern_colon = r'[:：]$'
        for idx, i in enumerate(list_block):
            i = xstr(Selector(text=i)).strip()
            if i != '':
                i = re.sub(pattern, '\n', i)
                if len(self.text_block) == 0:
                    self.text_block.append(i)
                else:
                    if re.match(pattern_colon, self.text_block[-1]) is None:
                        self.text_block.append(i)
                    else:
                        self.text_block[-1] += '\n'+i


    def get_dict(self) -> dict:
        d = vars(self)
        d.pop('pagedata', None)
        # d.pop('text_block', None)
        d['tag'] = list(d['tag'])
        d['class_stop'] = list(d['class_stop'])
        return d


def tc2sc(s: str) -> str:
    return converter.convert(s)


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
        # TODO: only convert text_block
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


def split_style_class(selector_text: str) -> list[str]:
    operation = set('~+>')
    list_name = []
    name = ''
    for idx_k, k in enumerate(selector_text):
        if k == ' ':
            k_left = selector_text[idx_k-1]
            k_right = selector_text[idx_k+1]
            if k_right in operation:
                pass
            else:
                if k_left in operation:
                    pass
                # seperation of two class
                else:
                    list_name.append(name.strip())
                    name = ''
        elif k == ',':
            continue
        name += k
    list_name.append(name.strip())
    return list_name


def parse_style_border(
    pagedata: Selector,
    # dir_wikidot: str = DIR_WIKIDOT,
    style_valid: set = set(['.alt-block']),
) -> set[str]:
    cssutils.log.setLevel(logging.FATAL)
    list_rule = []
    for i in xstr(pagedata.css('style'), False):
        if 'border: ' not in i or '{' not in i:
            continue
        name = i.split('{')[0]
        for i in style_valid:
            for j in ' ,':
                if i+j in name:
                    continue
        for j in cssutils.parseString(i):
            if j.typeString == 'STYLE_RULE':
                list_rule.append(j)
            # print(j.typeString)
            # TODO: import other css in IMPORT_RULE
            # elif j.typeString == 'IMPORT_RULE':
            #     try:
            #         list_rule += load_css_href(j.href, dir_wikidot)
            #     except:
            #         pass
    set_null = set(['0', 'none'])
    for i in list_rule:
        # print(j)
        list_name = split_style_class(i.selectorText)
        for name in list_name:
            if name in style_valid:
                continue
        for property in i.style.getProperties():
            if property.name == 'border':
                if property.value not in set_null:
                    for name in list_name:
                        style_valid.add(name)
    return style_valid


def unfold(
    selector_list: SelectorList[Selector],
    class_stop: set[str],
    style_stop: set[str] = set(['border']),
) -> SelectorList[Selector]:
    selector_unfolded = SelectorList()
    for selector in selector_list:
        # stop unfolding when one of class_stop found
        stop_by_class = False
        for i in selector.xpath('@class').extract():
            if i in class_stop:
                stop_by_class = True
                break
        # stop unfolding when one of style_stop found
        stop_by_style = False
        style = selector.xpath('@style').extract_first()
        if style is not None:
            for i in style_stop:
                if i in style:
                    stop_by_style = True
                    break
        # stop unfolding if root.tag is not div
        if selector.root.tag != 'div' or stop_by_class or stop_by_style:
            selector_unfolded.append(selector)
        else:
            selector_unfolded += unfold(selector.xpath('*'), class_stop)
        # print(selector_unfolded)
    return selector_unfolded

# cssutils.parseFile(css_path) may take forever for some css files


def unfold_colmod(page_content: SelectorList) -> SelectorList:
    colmod_block = page_content.css('div.colmod-block')
    if len(colmod_block) == 0:
        return page_content
    all_text = page_content.extract()[0]
    for block in colmod_block:
        block_text = block.extract()
        content_text = block.css('div.colmod-content').extract()[0]
        all_text = all_text.replace(block_text, content_text)

    page_content = SelectorList([Selector(text=all_text)])
    return page_content



if __name__ == '__main__':
    address = 'scp-cn-1285'
    # address = 'scp-6009'
    html_file = f'../SCP-CN/scp-wiki-cn.wikidot.com/{address}.html'
    # html_file = f'SCP-CN/scp-wiki-cn.wikidot.com/{address}.html'


    list_html = scan_html(n_limit=None)
    result = save_page(list_html)

    # page = Page(html_file)
    # page.update_text_block()
    # text_block = page.text_block
    # for i in text_block:
        # print(i)

    # with open(html_file) as f:
    #     pagedata = Selector(text=f.read())


    # style_valid = parse_style(pagedata)
    # class_stop = set([i[1:] for i in style_valid if i.startswith('.')])
    # i_list =  pagedata.css('div#page-content').xpath('*')
    # list_unfolded = unfold(i_list, class_stop)