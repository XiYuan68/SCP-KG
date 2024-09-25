# -*- encoding: utf-8 -*-
'''
@File    :   series.py
@Time    :   2024/07/17 17:58:48
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''


import re
from string import printable
import json
from urllib import parse
from collections import OrderedDict

from scrapy.selector import Selector

from page import Page
from utilities import DIR_WIKIDOT, strip_address, xstr, xhref, save_json


PATTERN_HUB = r'\s*中心.?$'


def parse_series_simple(title: Selector) -> dict:
    dict_series = {}
    dict_series['name'] = re.sub(PATTERN_HUB, '', xstr(title))
    dict_series['address'] = strip_address(xhref(title))
    dict_series['description'] = None
    dict_series['tag'] = None
    return dict_series


def parse_tag_in_hub(
    dict_series: dict,
    dir_wikidot = DIR_WIKIDOT,
) -> str | None:
    if dict_series['tag'] is not None:
        return dict_series['tag']
    name = dict_series['name']
    address = dict_series['address']
    html = dir_wikidot + address + '.html'
    tag = Page(html).tag
    if name in tag:
        dict_series['tag'] = name

    return dict_series


def parse_series(
    html_file = DIR_WIKIDOT + 'series-archive.html'
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
    list_series = []
    # series with tag
    wrapper = Selector(text=htmlhandle).css('div[class="series-wrapper large"]')
    for block in wrapper.xpath('*'):
        dict_series = {}
        title = block.css('h3')
        dict_series['name'] = xstr(title)
        dict_series['address'] = strip_address(xhref(title))
        dict_series['description'] = xstr(block.css('div.blurb'))
        tag = xhref(block.css('div.tag-lead'))
        tag = strip_address(parse.unquote(tag).split('/')[-1])
        dict_series['tag'] = tag
        dict_series['language'] = '英文站'
        list_series.append(dict_series)
    # series with no tag
    wrapper = Selector(text=htmlhandle).css('div[class="series-wrapper content-type-description"]')
    list_block = wrapper.xpath('*')[:-1]
    list_html = xhref(wrapper.css('div.pager'), False)
    for i in list_html[:-1]:
        with open(DIR_WIKIDOT+i) as htmlfile:
            htmlhandle = htmlfile.read()
        wrapper = Selector(text=htmlhandle).css('div[class="series-wrapper content-type-description"]')
        list_block += wrapper.xpath('*')[:-1]
    
    for block in list_block:
        dict_series = parse_series_simple(block.css('div.title'))
        dict_series['language'] = '英文站'
        dict_series = parse_tag_in_hub(dict_series)
        list_series.append(dict_series)
    
    return list_series


def parse_series_cn(
    html_file: str = DIR_WIKIDOT + 'series-archive-cn.html',
) -> list[dict]:
    with open(html_file) as htmlfile:
        pagedata = Selector(text=htmlfile.read())
    list_tr = pagedata.css('tr')[2:]
    for i in pagedata.css('div.pager').css('span.target')[:-1]:
        html_file = DIR_WIKIDOT + xhref(i)
        with open(html_file) as htmlfile:
            pagedata = Selector(text=htmlfile.read())
        list_tr += pagedata.css('tr')[2:]
    list_series = []
    for tr in list_tr:
        dict_series = parse_series_simple(tr.css('td')[0])
        dict_series['language'] = '中文分部'
        dict_series = parse_tag_in_hub(dict_series)
        list_series.append(dict_series)         

    return list_series


def parse_series_from_tag(
    list_series: list[dict],
    json_tag: str = '../data/tag.json',
) -> list[dict]:
    set_tag = set([i['tag'] for i in list_series if i['tag'] is not None])
    with open(json_tag) as f:
        list_dict_tag = json.load(f)
    list_series_from_tag = []
    for i in list_dict_tag:
        if "故事系列" in i['type'] and i['tag'] not in set_tag:
            dict_series = {}
            dict_series['name'] = i['tag']
            dict_series['address'] = i['address']
            dict_series['description'] = i['description']
            dict_series['tag'] = i['tag']
            language: list[str] = i['type']
            for j in ["故事系列", "其他语言分部"]:
                if j in language:
                    language.remove(j)
            dict_series['language'] = language[0]
            list_series_from_tag.append(dict_series)
    return list_series_from_tag


if __name__ == '__main__':
    list_series = parse_series()
    list_series += parse_series_cn()
    list_series += parse_series_from_tag(list_series)
    save_json(list_series, '../data/series.json')
   