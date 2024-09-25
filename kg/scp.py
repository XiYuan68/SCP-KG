# -*- encoding: utf-8 -*-
'''
@File    :   scp.py
@Time    :   2024/07/10 23:43:47
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

import re
import json

from joblib import Parallel, delayed

from page import Page, XPATH_CONTENT


# TODO: filtering scp and description without common keywords
# about 300-500 SCP-objects do not use '特殊收容措施' and '描述' as keywords
# or has no scp or description at all
KWD_SCP = [
    '收容措施',
    '特别收容措施',
    '当前状态',
    '特殊收容等级',
    '特殊收容措施（已归档）',
]
KWD_DESCRIPT = [
    '描述',
    '项目描述',
    '概要',
    '描述（已归档）',
]
KEY_SORTED = [
    'item_number',
    'special_containment_procedure',
    'description',
    'tag',
    'address',
    'idx_mainpage',
]

class ScpObject():
    def __init__(
        self,
        list_page: list[Page],
    ) -> None:
        self.list_page = list_page
        self.update_mainpage()
        for i in KWD_SCP:
            for j in KWD_DESCRIPT:
                if self.scp is None or self.description is None:
                    self.update_mainpage(i, j, self.scp, self.description)
        self.tag = self.list_page[self.idx_mainpage].tag
        # self.update_object_class()
        self.item_number = self.list_page[0].address
        self.address = [i.address for i in self.list_page]


    # def update_object_class(self) -> None:
    #     self.object_class = None
    #     for i in OBJECT_CLASS:
    #         if i in self.tag:
    #             self.object_class = i
    #             break
    
        
    def update_mainpage(
        self,
        kwd_scp: str = '特殊收容措施',
        kwd_description: str = '描述',
        scp: str = None,
        description: str = None,
    ) -> None:
        # special_containment_procedures 特殊收容措施
        self.scp = scp
        # 描述
        self.description = description

        main_page = None
        # assume latest scp&description are always in the last page
        for idx, i in enumerate(self.list_page[::-1]):
            # assume latest(true) scp&description are always at the lower part of the page
            # corner-case: scp-cn-2849
            for idx_j, j in enumerate(i.text_block):
                # collecting scp until description met
                if self.scp is None and j.startswith(kwd_scp):
                    self.scp = j
                    for k in i.text_block[idx_j+1:]:
                        if not k.startswith(kwd_description):
                            self.scp += k
                        else:
                            break
                if self.description is None and j.startswith(kwd_description):
                    self.description = j
                    # in case that the whole block is just kwd_description
                    if len(self.description) < 5:
                        try:
                            self.description += i.text_block[idx_j+1]
                        except Exception:
                            pass
                if self.scp is not None and self.description is not None:
                    main_page = i
                    self.idx_mainpage = len(self.list_page) - idx - 1
                    break
            if main_page is not None:
                break
        if main_page is None:
            main_page = self.list_page[0]
            self.idx_mainpage = 0

        # print(self.scp)
        # print(self.description)

        # the scp-block is always above the description-block
        # look for undiscovered scp
        if self.scp is None and self.description is not None:
            if self.description in main_page.text_block:
                idx = main_page.text_block.index(self.description)
                for i in range(idx):            
                    block = main_page.text_block[i]
                    if kwd_scp in block:
                        scp_block = ''.join(main_page.text_block[i:idx])
                        text_split = scp_block.split(kwd_scp)
                        self.scp = kwd_scp.join(text_split[1:]).replace('\n', '')
                        break


        # in case kwd_scp or kwd_description are in seperated blocks
        if isinstance(self.scp, str) and len(self.scp) < 20:
            self.scp = None
        if isinstance(self.description, str) and len(self.description) < 20:
            self.description = None
        # print(self.scp)
        # print(self.description)

        # remove 特殊收容措施 or 描述 at the beginning of the string
        if self.scp is not None:
            for pattern in ['^'+kwd_scp, r'^[\:：]?\s?']:
                self.scp = re.sub(pattern, '', self.scp)
        if self.description is not None:
            for pattern in ['^'+kwd_description, r'^[\:：]?\s?']:
                self.description = re.sub(pattern, '', self.description)



        # find containment site in scp, then description
        # self.containment_site = None
        # if self.scp is not None:
        #     pattern = r'site-[0-9]+[0-9\-]*'
        #     result = re.findall(pattern, self.scp, re.I)
        #     if len(result) > 0:
        #         self.containment_site = result[0]
        #     for i in result[1:]:
        #         if len(i) > len(self.containment_site):
        #             self.containment_site = i
        # if self.containment_site is None:
        #     pattern = r'site-[0-9]+[0-9\-]*'
        #     result = re.findall(pattern, self.description, re.I)
        #     if len(result) > 0:
        #         self.containment_site = result[0]
        #     for i in result[1:]:
        #         if len(i) > len(self.containment_site):
        #             self.containment_site = i

    def update_mainpage_rawtext(
        self,
        kwd_scp: str = '特殊收容措施',
        kwd_description: str = '描述',
        scp: str = None,
        description: str = None,
    ) -> None:
        # special_containment_procedures 特殊收容措施
        self.scp = scp
        # 描述
        self.description = description

        # looking for SCP and description in raw text
        # which is the least accurate way
        if self.scp is None or self.description is None:
            # text_block = [i for i in main_page.text.split('\n') if i!='']
            # text_block = main_page.text.split('\n')
            text_block = []
            for i in self.main_page.text_block:
                text_block += i.split('\n')
            for idx_j, j in enumerate(text_block):
                if self.scp is None and j.startswith(kwd_scp):
                    self.scp = j
                    for k in text_block[idx_j:]:
                        if not k.startswith(kwd_description):
                            self.scp += k
                        else:
                            break
                # TODO: extend description more than one block
                if self.description is None and j.startswith(kwd_description):
                    self.description = j
                    if len(self.description) < 5:
                        try:
                            self.description += text_block[idx_j+1]
                        except Exception:
                            pass
                if self.scp is not None and self.description is not None:
                    break


    def update_mainpage_blbf(
        self,
        list_html: list[str],
    ) -> None:
        # block of special-containment-procedures and description with no keyword text
        # such as div.blbf-special-containment-procedures blbf-classic
        # and div.blbf-description blbf-classic
        list_page = [Page(i) for i in list_html]
        for idx, p in enumerate(list_page):
            for i in p.pagedata.xpath(XPATH_CONTENT + '/*/div')[::-1]:
                div_class: str = i.xpath('@class').extract_first()
                if self.scp is None and isinstance(div_class, str):
                    if div_class.startswith('blbf-special-containment-procedures'):
                        self.scp = i.xpath('string(.)').extract_first().replace('\n', '')
                if self.description is None and isinstance(div_class, str):
                    if div_class.startswith('blbf-description'):
                        self.description = i.xpath('string(.)').extract_first().replace('\n', '')
                if self.scp is not None and self.description is not None:
                    self.idx_mainpage = len(list_page) - idx - 1
                    break
    

    def get_dict(self) -> dict:
        d = vars(self)
        # d['list_page'] = [i.get_dict() for i in self.list_page]
        d.pop('list_page')
        # easier for llm to understand and cypher generation
        d['special_containment_procedure'] = d['scp']
        d.pop('scp')
        d['tag'] = list(d['tag'])
        d_sorted = {key: d[key] for key in KEY_SORTED}
        return d_sorted
    

def get_scp_dict(list_page: list[Page]) -> dict:
    return ScpObject(list_page).get_dict()


def save_all_scp(
    list_page_all: list[list[Page]],
    scp_json: str = '../data/scp.json',
) -> list[dict]:
    print('Parsing all SCP objects')
    pool = Parallel(-1)
    result = [i for i in pool(delayed(get_scp_dict)(j) for j in list_page_all)]
    with open(scp_json, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('All SCP objects Parsed')
    return result


def check(
    result: list[dict],
    json_no_scp: str = '../data/scp_no_scp.json',
    json_no_description: str = '../data/scp_no_description.json',
) -> tuple[list[str]]:
    n_object = len(result)
    n_scp = 0
    list_no_scp = []
    n_description = 0
    list_no_description = []
    for i in result:
        if i['special_containment_procedure'] is not None and len(i['special_containment_procedure']) > 5:
            n_scp += 1
        else:
            list_no_scp.append(i['item_number'])
        if i['description'] is not None and len(i['description']) > 5:
            n_description += 1
        else:
            list_no_description.append(i['item_number'])
    print(f'''#SCP-object without SCP: {n_scp}/{n_object}
#SCP-object without desciption: {n_description}/{n_object}''')
    with open(json_no_scp, 'w') as f:
        json.dump(list_no_scp, f, indent=2)
    with open(json_no_description, 'w') as f:
        json.dump(list_no_description, f, indent=2)

    return list_no_scp, list_no_description


if __name__ == '__main__':
    address = 'scp-1949'
    html = f'../SCP-CN/scp-wiki-cn.wikidot.com/{address}.html'

    # page = Page(html)
    # page.update_link()
    # page.update_text_block()
    # list_page_all = [[page]]
    # for i in list_page_all:
    #     scp_object = ScpObject(i)
    #     print('特殊收容措施：', scp_object.scp)
    #     print('描述：', scp_object.description)
    #     print('标签：', scp_object.tag)
    #     print('编号：', scp_object.item_number)
    #     print('-'*30)



    # main_page = scp_object.list_page[scp_object.idx_mainpage]
    # text_block = main_page.text_block

    from page import get_page_from_json
    list_page_all = get_page_from_json()
    result = save_all_scp(list_page_all)
    list_no_scp, list_no_description = check(result)

