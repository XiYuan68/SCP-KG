# -*- encoding: utf-8 -*-
'''
@File    :   attribute.py
@Time    :   2024/08/27 22:04:19
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

import json
import re

from utilities import save_json


def parse_attribute_from_tag(
    json_tag: str = '../data/tag.json',
) -> list[dict]:
    with open(json_tag) as f:
        list_dict_tag: list[dict] = json.load(f)
    list_attribute = []
    pattern = r'.*（.*）$'
    for i in list_dict_tag:
        if "特性标签" in i['type']:
            dict_attribute = i
            dict_attribute['name'] = i['tag']
            dict_attribute.pop('address')
            list_type = dict_attribute['type']
            dict_attribute['type'] = None
            if len(list_type)==2 and '特性标签' in list_type:
                list_type.remove('特性标签')
                t = list_type[0]
                if re.match(pattern, t) is not None:
                    dict_attribute['type'] = re.sub(r'（.*）$', '', t)
                elif t == "未分類":
                    dict_attribute['type'] = t
            list_attribute.append(dict_attribute)
    return list_attribute


if __name__ == '__main__':
    list_attribute = parse_attribute_from_tag()
    save_json(list_attribute, '../data/attribute.json')