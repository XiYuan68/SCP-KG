# -*- encoding: utf-8 -*-
'''
@File    :   utilities.py
@Time    :   2024/07/17 18:47:02
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''


DIR_WIKIDOT = '../SCP-CN/scp-wiki-cn.wikidot.com/'

import re
import json
from urllib.parse import unquote

from scrapy import Selector

def save_json(
    obj,
    json_path: str,
    ) -> None:
    with open(json_path, 'w') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_json(
    json_path: str,
    ):
    with open(json_path) as f:
        return json.load(f)
    

def strip_address(s: str | None) -> str:
    if s is None:
        return s
    if 'wikidot.com/' in s:
        s = s.split('wikidot.com/')[-1]
    pattern_html = r'\.html.*$'
    pattern_path = r'^.*\.\./' 
    s = re.sub(pattern_html, '', s)
    s = re.sub(pattern_path, '', s)
    return s


def xstr(
    s: Selector,
    first: bool = True,
) -> str:
    if first:
        s = s.xpath('string(.)').extract_first()
        if isinstance(s, str):
            s = s.strip()
        return s
    else:
        return s.xpath('string(.)').extract()


def xhref(
    s: Selector,
    first: bool = True,
) -> str|None|list[str]:
    if first:
        return s.xpath('descendant::a/@href').extract_first()
    else:
        return s.xpath('descendant::a/@href').extract()
    

def strip_tag(s: str | None):
    if s is None or not s.startswith('system_page-tags/tag/'):
        return None
    pattern_tag = r'^system_page-tags/tag/'
    pattern_html = r'\.html.*$'
    s = re.sub(pattern_tag, '', s)
    s = re.sub(pattern_html, '', s)
    s = unquote(s)
    return s

def strip_quote(s: str) -> str:
    if s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    return s