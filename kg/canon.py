# -*- encoding: utf-8 -*-
'''
@File    :   canon.py
@Time    :   2024/07/17 16:00:59
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

from utilities import DIR_WIKIDOT, strip_quote, xstr, xhref, save_json, strip_tag


def parse_canon(
    html_file = DIR_WIKIDOT + 'canon-hub.html',
    language: str = '英文站',
    json_tag: str = '../data/tag.json'
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
    if language == '英文站':
        canon_wrapper = Selector(text=htmlhandle).css('div.canon-wrapper')
        list_block = canon_wrapper.xpath('*')
    else:
        list_block = Selector(text=htmlhandle).css('div[class="content-panel centered standalone series"]')
    
    with open(json_tag) as f:
        list_dict_tag = json.load(f)
    # tags that cannot be found in tag_guide page
    address2tag = {
        'daybreak': '破晓',
        'lampeter-hub': '兰彼得',
        'seas-of-orcadia-hub': 'orcadia',
        'simulacrum-project-hub': '幻象计划',
        'unhuman-hub': '非人类',
    }
    for i in list_dict_tag:
        if "设定" in i['type'] and i['address'] is not None:
            address2tag[i['address']] = i['tag']
    
    list_canon = []
    for block in list_block:
        dict_canon = {}
        title = block.css('h1')
        if len(title) == 0:
            title = block.css('h2')
        dict_canon['name'] = xstr(title)
        dict_canon['address'] = xhref(title)[:-5]
        dict_canon['description'] = xstr(block.css('p'))
        dict_canon['language'] = language
        dict_canon['tag'] = None
        if dict_canon['address'] in address2tag.keys():
            dict_canon['tag'] = address2tag[dict_canon['address']]

        list_canon.append(dict_canon)
    return list_canon


def parse_canon_from_tag(
    list_canon: list[dict],
    json_tag: str = '../data/tag.json',
) -> list[dict]:
    set_tag = set([i['tag'] for i in list_canon if i['tag'] is not None])
    with open(json_tag) as f:
        list_dict_tag = json.load(f)
    list_canon_from_tag = []
    for i in list_dict_tag:
        if "设定" in i['type'] and i['tag'] not in set_tag:
            dict_canon = {}
            dict_canon['name'] = i['tag']
            dict_canon['address'] = i['address']
            dict_canon['description'] = i['description']
            language: list[str] = i['type']
            for j in ["设定", "其他语言分部"]:
                if j in language:
                    language.remove(j)
            dict_canon['language'] = language[0]
            dict_canon['tag'] = i['tag']

            list_canon_from_tag.append(dict_canon)
    return list_canon_from_tag


if __name__ == '__main__':
    list_canon = parse_canon()
    list_canon += parse_canon(DIR_WIKIDOT + 'canon-hub-cn.html', '中文分部')
    list_canon += parse_canon_from_tag(list_canon)
    save_json(list_canon, '../data/canon.json')