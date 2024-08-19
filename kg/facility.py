# -*- encoding: utf-8 -*-
'''
@File    :   facility.py
@Time    :   2024/07/16 15:36:54
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


def parse_facility(
    html_file = DIR_WIKIDOT + 'secure-facilities-locations.html',
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    list_facility = []
    for i in page_content.css('div.s-wrapper').css('div.socontent'):
        dict_facility = {}
        # pattern = r'site-[0-9]+[-0-9]*|area-[0-9]+[-0-9]*'
        pattern = r'site-.*|area-[0-9]+[-0-9]*'
        title = i.css('h1').xpath('string(.)').extract_first()
        title = re.findall(pattern, title, re.I)
        if len(title) > 0:
            dict_facility['name'] = title[0].lower()
        p_text = i.xpath('p').xpath('string(.)').extract()
        location = p_text[0].strip()
        if location.startswith('地点：'):
            dict_facility['location'] = location[3:]
            p_text.pop(0)
        dict_facility['description'] = '\n'.join(p_text)
        dict_facility['dossier'] = None
        dict_facility['object_related'] = set()
        dict_facility['object_contained'] = set()
        dict_facility['incident'] = set()
        dict_facility['language'] = '英文站'

        # 被收容在该设施中的项目
        during_object_contained = False
        for j in i.css('a'):
            link = j.xpath('@href').extract_first()
            text = j.xpath('string(.)').extract_first()
            # print(text, link)
            if link.endswith('.html'):
                link = parse.unquote(link[:-5])
                if link.startswith('scp-'):
                    if during_object_contained:
                        dict_facility['object_contained'].add(link)
                    else:
                        during_object_contained = False
                        dict_facility['object_related'].add(link)
                else:
                    for k in ['档案', '中心页']:
                        if k in text and dict_facility['dossier'] is None:
                            dict_facility['dossier'] = link
                            break
                    else:
                        dict_facility['incident'].add(link)
            else:
                if text.endswith('被收容在该设施中的项目：'):
                    during_object_contained = True

        for k, v in dict_facility.items():
            if isinstance(v, set):
                dict_facility[k] = list(v)
        # print(dict_facility)
        list_facility.append(dict_facility)
        # print(text2link)
    return list_facility


def parse_facility_complete(
    html_file = DIR_WIKIDOT + 'facilities-complete-list.html'
) -> list[dict]:
    head2attr = {}
    head2attr['站点'] = 'site'
    head2attr['区域'] = 'area'
    head2attr['设施'] = 'facility'
    head2attr['名称'] = 'name'
    head2attr['描述'] = 'description'
    head2attr['已收容项目'] = 'object_contained'
    head2attr['值得注意的事件'] = 'incident'
    head2attr['已收容项目/值得注意的事件'] = 'object_contained/incidient'
    head_facility_type = set(['站点', '区域', '设施'])


    
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    list_row = []
    for table in page_content.css('table.wiki-content-table')[1:-1]:
        head = table.css('th').xpath('string(.)').extract()
        for row in table.css('tr'):
            dict_row = {}
            for h, col in zip(head, row.css('td')):
                text = '\n'.join(col.xpath('string(.)').extract())
                link = col.xpath('a/@href').extract()
                link = [i[:-5] for i in link if i.endswith('.html')]
                key = head2attr[h]
                if h in head_facility_type:
                    # special facility type for outpost and observation_post
                    if key == 'facility':
                        if 'Observation Post' in text:
                            key = 'observation_post'
                        else:
                            for i in ['前哨站', 'Outpost']:
                                if i in text:
                                    key = 'outpost'
                                    break
                    dict_row['type'] = key
                    dict_row['number'] = text
                elif h == '名称':
                    dict_row['name'] = text
                else:
                    dict_row[key] = {
                        'text': text,
                        'link': link,
                    }
            if dict_row != {}:
                list_row.append(dict_row)    
    return list_row


def parse_facility_cn(
    html_file = DIR_WIKIDOT + 'secure-facilities-locations-cn.html',
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    
    list_facility = []
    dict_facility = {}
    set_prefix = set(['site', 'area'])
    set_tag = set(['span', 'p'])
    facility_child_count = -1
    for child in page_content.xpath('*'):
        for prefix in set_prefix:
            if child.xpath('@class').extract_first() == prefix + 'Icon':
                if len(dict_facility) > 0:
                    dict_facility['description'] = '\n'.join(dict_facility['description'])
                    for k, v in dict_facility.items():
                        if isinstance(v, set):
                            dict_facility[k] = list(v)
                    list_facility.append(dict_facility)
                dict_facility = {}
                dict_facility['name'] = None
                dict_facility['location'] = None
                dict_facility['description'] = None
                dict_facility['dossier'] = None
                dict_facility['object_related'] = set()
                dict_facility['object_contained'] = set()
                dict_facility['incident'] = set()
                dict_facility['language'] = '中文分部'

                facility_child_count = 0
                break
        if child.root.tag not in set_tag or facility_child_count < 0:
            continue
        elif facility_child_count == 0:
            facility_child_count += 1
            continue
        # facility name (and dossier)
        elif facility_child_count == 1:
            dict_facility['name'] = xstr(child.css('strong'))
            dict_facility['dossier'] = strip_address(xhref(child))
            facility_child_count += 1
            continue
        # description
        else:
            if dict_facility['description'] is None:
                dict_facility['description'] = []
            dict_facility['description'].append(xstr(child))
            for i in xhref(child, False):
                i = strip_address(i)
                if i.startswith('scp-'):
                    dict_facility['object_contained'].add(i)
                else:
                    dict_facility['incident'].add(i)
    if len(dict_facility) > 0:
        dict_facility['description'] = '\n'.join(dict_facility['description'])
        for k, v in dict_facility.items():
            if isinstance(v, set):
                dict_facility[k] = list(v)
        list_facility.append(dict_facility)

    return list_facility


if __name__ == '__main__':
    list_facility = parse_facility()
    list_facility += parse_facility_cn()
    # list_facility_complete = parse_facility_complete()
    save_json(list_facility, '../data/facility.json')
    # save_json(list_facility_complete, '../data/facility_complete.json')
    

