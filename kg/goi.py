# -*- encoding: utf-8 -*-
'''
@File    :   goi.py
@Time    :   2024/07/16 00:47:23
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

import re
from string import printable
import json
from urllib import parse

from scrapy.selector import Selector

from utilities import DIR_WIKIDOT, strip_address, xstr, xhref, save_json


ADDRESS_LANGUAGE = [
    'groups-of-interest',
    'groups-of-interest-ko',
    'groups-of-interest-cn',
    # 标签在 goi-complete-list 中
    'groupes-d-interet-fr',
    # 波兰语
    'groups-of-interest-pl',
    # 西班牙语
    'grupos-de-interes-hispanoparlantes',
    # 泰语
    'groups-of-interest-th',
    'groups-of-interest-jp',
    # 德语
    'interessengruppen',
    # 乌克兰语
    'groups-of-interest-ua',
    # 葡萄牙语
    'grupos-de-interesse',
    # 意大利语
    'gruppi-di-interesse',
    # 俄语
    'groups-of-interest-of-the-russian-branch',
]


def get_address2text(
    html_file: str = DIR_WIKIDOT + 'goi-complete-list.html',
) -> dict:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    address2text = {}
    for i in page_content.css('a'):
        link = i.xpath('@href').extract_first()
        if isinstance(link, str) and link.endswith('.html'):
            link = link[:-5]
            text = i.xpath('text()').extract_first()
            if link not in address2text.keys():
                address2text[link] = text
    address2text['groups-of-interest'] = '英文站相关组织'
    return address2text


def parse_goi(
    address2text: dict,
    html_file: str = DIR_WIKIDOT + 'groups-of-interest.html',
) -> list[dict]:
    # print(html_file)
    language_address = html_file.split('scp-wiki-cn.wikidot.com/')[-1]
    language_address = language_address.split('.html')[0]
    language = address2text.get(language_address, None)
    if isinstance(language, str):
        language = language.replace('相关组织', '')

    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    tag_start = 'system_page-tags/tag/'
    list_goi = []
    list_panel = page_content.xpath('div[@class="content-panel standalone series"]')
    if 'groups-of-interest-of-the-russian-branch' not in html_file:
        list_panel.pop(0)
    if 'grupos-de-interesse' in html_file:
        list_panel.pop(0)
    # print(len(list_panel))

    pattern_description = r'^概.[：\:]?\s*'
    for i in list_panel:
        # key: name_chinese, name_english, address, description, tag
        dict_goi = {'language': language}
        address = i.xpath('*/span/a/@href').extract_first()
        if isinstance(address, str):
            address = address[:-5]
        dict_goi['address'] = address
        dict_goi['name'] = i.xpath('*/span/a/text()').extract_first()
        if dict_goi['name'] is None:
            # dict_goi['name'] = i.xpath('*/span/text()').extract_first()
            dict_goi['name'] = i.css('span').xpath('text()').extract_first()
        # special process for 瓦尔拉文公司（Valravn Corporation）
        pattern = r'[\(（].*[）\)]$'
        # print(dict_goi['name'])
        if dict_goi['name'] is None:
            continue
        alias_in_chi = re.findall(pattern, dict_goi['name'])
        if len(alias_in_chi) > 0:
            alias_in_chi = alias_in_chi[0]
            dict_goi['name'] = dict_goi['name'].replace(alias_in_chi, '')
            dict_goi['alias'] = alias_in_chi[1:-1]
        else:
            alias = i.xpath('*/span/text()').extract_first()
            if alias is None or alias == dict_goi['name']:
                dict_goi['alias'] = None
            else:
                dict_goi['alias'] = alias[1:-1]
        # print(dict_goi['name'])
        # print(dict_goi['english'])
        description = i.xpath('p').xpath('string(.)').extract()[:-1]
        description = '\n'.join(description)
        description = re.sub(pattern_description, '', description)
        dict_goi['description'] = description

        dict_goi['tag'] = None
        if 'grupos-de-interesse' in html_file:
            tag = i.xpath('p').xpath('string(.)').extract()[-1]
            tag = tag.replace('标签：', '')
            dict_goi['tag'] = tag
        elif 'gruppi-di-interesse' in html_file:
            dict_goi['tag'] = dict_goi['name']
        else:
            all_link = i.xpath('*/a/@href')
            if len(all_link) > 0:
                last_link = i.xpath('*/a/@href')[-1].extract()
                if last_link.startswith(tag_start):
                    last_link = last_link.split(tag_start)[-1]
                    last_link = last_link.split('.html')[0]
                    dict_goi['tag'] = parse.unquote(last_link)
        # print(dict_goi['tag'])

        list_goi.append(dict_goi)
    return list_goi


def parse_goi_complete(
    html_file: str = DIR_WIKIDOT + 'goi-complete-list.html'
) -> list[dict]:
    pass


if __name__ == '__main__':
    address2text = get_address2text()
    html_file: str = DIR_WIKIDOT + 'goi-complete-list.html'
    list_goi = []
    for i in ADDRESS_LANGUAGE:
        list_goi += parse_goi(address2text, DIR_WIKIDOT + f'{i}.html')
    save_json(list_goi, '../data/goi.json')
