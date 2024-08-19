# -*- encoding: utf-8 -*-
'''
@File    :   charactor.py
@Time    :   2024/07/17 01:30:36
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


def empty_dict_character() -> dict:
    dict_character = {}
    dict_character['name'] = None
    # dict_character['address'] = []
    dict_character['tag'] = None
    dict_character['alias'] = []
    dict_character['name_extra'] = []
    dict_character['address_extra'] = []
    dict_character['description'] = []
    dict_character['description_link'] = []
    dict_character['type'] = None
    return dict_character


def split_quote(alias_all: str) -> list[str]:
    list_alias = []
    alias = ''
    in_word = False
    for ch in alias_all:
        if ch == '"':
            in_word = alias==''
            if not in_word:
                list_alias.append(alias)
                alias = ''
        elif in_word:
            alias += ch
    return list_alias


def parse_character(
    html_file = DIR_WIKIDOT + 'personnel-and-character-dossier.html',
    o5: bool = False,
) -> list[dict]:
    with open(html_file) as htmlfile:
        htmlhandle = htmlfile.read()
        page_content = Selector(text=htmlhandle).css('div#page-content')[0]
    list_character = []
    title = page_content.css('ul.yui-nav').xpath('*')
    content = page_content.css('div.yui-content').xpath('*')
    for t, c in zip(title, content):
        # print(t)
        t_text = t.xpath('string(.)').extract_first()
        if o5:
            if not t_text.startswith('O5-') and t_text!='管理员':
                continue

        dict_character = empty_dict_character()
        below_hr = True
        for row in c.xpath('*'):
            extract = row.extract()
            text = row.xpath('string(.)').extract_first()
            link_text = row.css('a').xpath('string(.)').extract()
            link_address = row.css('a').xpath('@href').extract()
            if extract.startswith('<p style="text-align: center;">'):
                continue
            if extract == '<hr>':
                if dict_character['name'] is not None:
                    dict_character['description'] = '\n'.join(dict_character['description'])
                    list_character.append(dict_character)
                dict_character = empty_dict_character()
                below_hr = True
            else:
                # first row of a block
                # should starts with the name of the charater
                if below_hr:
                    below_hr = False
                    # for O5 dossiers, text of the first line is always like:
                    # O5-1："奠基人"。
                    # O5-11："看守"，或"狱卒"。 [叛逃]
                    # corner-case: 管理员："Ethan Horowitz"。
                    if o5:
                        if text.count('：') != 1:
                            continue
                        number, alias_all = text.split('：')
                        dict_character['name'] = number
                        dict_character['alias'] = split_quote(alias_all)
                        continue
                    # character not in O5 nor as administrator
                    else:
                        pattern_name = r'^[^：]*：'
                        pattern_aka = r'，又称'
                        name = re.findall(pattern_name, text)
                        if len(name) == 0:
                            continue
                        name = name[0][:-1]
                        # character name has a attached link
                        # record first name that attached with a tag
                        if len(link_text) > 0:
                            for idx, (t, l) in enumerate(zip(link_text, link_address)):
                                if 'tag' in l and t in name:
                                    dict_character['name'] = strip_quote(link_text.pop(idx))
                                    dict_character['tag'] = strip_tag(link_address.pop(idx))
                                    break

                        # one character may have more than one name (i.e. alias)
                        # or two character share the same block
                        for idx, (t, l) in enumerate(zip(link_text, link_address)):
                            if t in name:
                                dict_character['name_extra'].append(strip_quote(t))
                                address = parse.unquote(l[:-5])
                                dict_character['address_extra'].append(address)
                            else:
                                link_address = link_address[idx+1:]
                                break
                        # character name has not a attached link
                        if dict_character['name'] is None:
                            if pattern_aka in name:
                                dict_character['name'] = strip_quote(name.split(pattern_aka)[0])
                            else:
                                dict_character['name'] = strip_quote(name)
                        # alias seperated by pattern_aka
                        if pattern_aka in name:
                            for alias in name.split(pattern_aka):
                                alias = strip_quote(alias)
                                if dict_character['name'] != alias:
                                    dict_character['alias'].append(alias)

                        text = text[len(name)+1:]
                dict_character['description'].append(text)
                link_address = [parse.unquote(i[:-5]) for i in link_address if i.endswith('.html')]
                dict_character['description_link'] += link_address
                dict_character['type'] = t_text
    return list_character

if __name__ == '__main__':
    list_character = parse_character()
    list_character += parse_character(
        DIR_WIKIDOT + 'o5-command-dossier.html', 
        o5=True)
    save_json(list_character, '../data/character.json')