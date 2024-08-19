# -*- encoding: utf-8 -*-
'''
@File    :   taskforce.py
@Time    :   2024/07/16 04:43:16
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

from utilities import DIR_WIKIDOT, strip_address, xstr, xhref, save_json


text2attr = OrderedDict()
text2attr['已知部署'] = 'object_deployed'
text2attr['利用项目'] = 'object_utilized'
text2attr['协助收容的项目'] = 'object_contained'
text2attr['Action Reports'] = 'action_report'
text2attr['行动报告'] = 'action_report'


def parse_tf_single(
    title: str,
    description: str,
    list_seletor: list[Selector],
) -> dict:
    dict_tf = {}
    pattern = r'[\(（].*[）\)]$'
    alias = re.findall(pattern, title)
    # english site
    if len(alias) > 0:
        alias = alias[0]
        alias_endchi = alias.split('”-')
        alias_english = alias_endchi[0][2:]
        alias_chinese = alias_endchi[-1][:-1]
        dict_tf['alias_english'] = alias_english
        dict_tf['alias_chinese'] = alias_chinese
    # chinese site
    else:
        pattern = r'“.*”$'
        alias = re.findall(pattern, title)[0]
        dict_tf['alias_chinese'] = alias[1:-1]
        dict_tf['alias_english'] = None
    name = title.replace(alias, '').strip()
    dict_tf['name'] = name

    
    description = re.sub(r'^特遣队任务：', '', description)
    dict_tf['description'] = description

    for idx_j, j in enumerate(list_seletor):
        text = j.xpath('string(.)').extract_first()
        for t, a in text2attr.items():
            if text.startswith(t):
                address = xhref(list_seletor[idx_j+1], False)
                address = [k[:-5] for k in address if k.endswith('.html')]
                dict_tf[a] = address
                break
    for i in text2attr.values():
        if i not in dict_tf.keys():
            dict_tf[i] = []

    return dict_tf


def parse_tf(
    html_file = DIR_WIKIDOT + 'task-forces.html',
    language: str = '英文站',
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]

    list_tf = []
    list_panel = page_content.xpath('div[@class="content-panel standalone series"]')[1:]
    for i in list_panel:
        title = i.xpath('*/h1/span').xpath('string(.)').extract_first()
        if title != '其他MTF':
            description = xstr(i.xpath('p')[0])
            dict_tf = parse_tf_single(title, description, i.xpath('*'))
            dict_tf['language'] = language
            list_tf.append(dict_tf)
            # print(dict_tf)
        else:
            dict_data = {}
            list_seletor = []
            for idx_j, j in enumerate(i.xpath('*')):
                # print('-'*30)
                title = xstr(j.css('h2'))
                if title is not None:
                    dict_data['title'] = title
                    dict_data['description'] = xstr(i.xpath('*')[idx_j+2])
                    list_seletor = []
                end_block = xhref(j) == '#toc'
                if end_block:
                    dict_data['list_seletor'] = list_seletor
                    dict_tf = parse_tf_single(**dict_data)
                    dict_tf['language'] = language
                    list_tf.append(dict_tf)
                else:
                    list_seletor.append(j)
    return list_tf


if __name__ == '__main__':
    list_tf = parse_tf()
    list_tf += parse_tf(DIR_WIKIDOT + 'task-forces-cn.html', '中文分部')
    save_json(list_tf, '../data/taskforce.json')
