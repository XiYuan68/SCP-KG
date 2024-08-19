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
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
    if language == '英文站':
        canon_wrapper = Selector(text=htmlhandle).css('div.canon-wrapper')
        list_block = canon_wrapper.xpath('*')
    else:
        list_block = Selector(text=htmlhandle).css('div[class="content-panel centered standalone series"]')
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
        list_canon.append(dict_canon)
    return list_canon


if __name__ == '__main__':
    list_canon = parse_canon()
    # print(list_canon)
    list_canon += parse_canon(DIR_WIKIDOT + 'canon-hub-cn.html', '中文分部')
    # print(list_canon_cn)
    save_json(list_canon, '../data/canon.json')