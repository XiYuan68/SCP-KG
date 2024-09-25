# -*- encoding: utf-8 -*-
'''
@File    :   tag.py
@Time    :   2024/06/23 15:54:00
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

parse all tags and related info in https://scp-wiki-cn.wikidot.com/tag-guide
解析所有SCP标签及其相关信息
'''

import re
from string import printable
import json

from scrapy.selector import Selector

from utilities import DIR_WIKIDOT, save_json, load_json, strip_address


def get_tag_attribute(
    tag_type: str = '',
    short_description: str = '',
    description: str = '',
    tag_english: str = '',
    address: str = '',
    ) -> dict:
   
    return {
        'tag_type': tag_type, 
        'short_description': short_description, 
        'description': description,
        'tag_english': tag_english,
        'address': address,
        }


def split_tag_description(
    tag_description: Selector,
    ) -> tuple[str, str, str]:

    link = ''
    if isinstance(tag_description, Selector):
        # extract link if there is one and only one link in description
        list_link = tag_description.xpath('a/@href').extract()
        link = list_link[0] if len(list_link) == 1 else ''
        tag_description = tag_description.xpath('string(.)').extract_first()

    # 将 荒诞小说（absurdist-fiction） — 所描写事件 修改成
    # 荒诞小说 (absurdist-fiction) - 所描写事件
    # 特殊例子（只出现一次）：_无体裁（_genreless）：— 不适用任何体裁、背景设定和风格标签的故事。
    if re.match(r'^.*（.*）：?[\s]?—\s.*', tag_description) is not None:
        for x, y in [('）：', ') '), ('（', ' ('), ('）', ')'), ('—', '-')]:
            tag_description = tag_description.replace(x, y)

    splitted = tag_description.split(' - ')
    tag = splitted[0]
    if ' (' in tag:
        tag_chinese, tag_english = tag.split(' (')
        tag_chinese = tag_chinese.strip()
        tag_english = tag_english.replace(')', '').strip()       
    else:
        tag_chinese = tag.strip()
        tag_english = ''
    if len(splitted) > 1:
        description = (' - '.join(splitted[1:])).replace('\n', '').strip()
    else:
        description = ''
    return tag_chinese, tag_english, description, link


def parse_tag_guide(
    tag_guide_html: str = DIR_WIKIDOT+'tag-guide.html',
    ) -> list[dict]:
    # edit tag-guide.html before running this function:
    # 主要标签-原创 and 主要标签-搞笑 are in the same ul-block, split them into two ul-blocks
    with open(tag_guide_html) as htmlfile:
        htmlhandle = htmlfile.read()
        pagedata = Selector(text=htmlhandle)
    dict_description = {}
    list_tag: list[dict] = []

    # 主要标签
    # 特殊排版的标签
    tag_special = {
        '项目等级': {'xpath': 'li/ul/li', 'title': ['项目等级']},
        'int': {'xpath': 'li', 'title': ['翻译', '翻译来源', '官方分部']},
        'cy': {'xpath': 'li', 'title': ['翻译', '翻译来源', '非官方分部']},
    }
    for i in range(1, 7):
        xpath_nav = f'/html/body/div[1]/div/div[1]/div/div[2]/div[2]/div[4]/div[2]/ul/li[{i}]'
        title = pagedata.xpath(xpath_nav).xpath('string(.)').extract_first()
        #title = title.replace('标签', '')
        xpath = f'/html/body/div[1]/div/div[1]/div/div[2]/div[2]/div[4]/div[2]/div/div[{i}]'
        # 不属于特性标签的标签
        if title != '特性标签':

            # 挑选 h2 的文本作为标签子类型
            all_selector = pagedata.xpath(xpath+'/*')
            subtitle = ''
            content2subtitle = {}
            for j in all_selector:
                j_text = j.xpath('string(.)').extract_first()
                if 'h2' in j.extract():
                    subtitle = j_text
                else:
                    content2subtitle[j_text.strip()] = subtitle

            for j in pagedata.xpath(xpath + '/ul'):
                j_text = j.xpath('string(.)').extract_first().strip()
                tag_chinese, tag_english, description, link = split_tag_description(j)
                # tags of object-class and translation 项目等级和翻译标签
                if tag_chinese in tag_special.keys():
                    title_special = tag_special[tag_chinese]['title']
                    for li in j.xpath(tag_special[tag_chinese]['xpath']):
                        tag_chinese, tag_english, description, link = split_tag_description(li)
                        list_tag.append({
                            'tag': tag_chinese,
                            'tag_english': tag_english,
                            'description': description,
                            'address': link,
                            'type': ['主要标签'] + title_special,
                            })
                else:
                    list_type = [content2subtitle[j_text]]
                    if title == '最高层级标签':
                        list_type.insert(0, '最高层级标签')
                    list_tag.append({
                        'tag': tag_chinese,
                        'tag_english': tag_english,
                        'description': description,
                        'address': link,
                        'type': list_type,
                    })
        # SCP特性标签
        else:
            # 挑选 h2或h3 的文本作为特性类型
            all_selector = pagedata.xpath(xpath+'/*')
            subtitle = ''
            content2subtitle = {}
            for j in all_selector:
                j_text = j.xpath('string(.)').extract_first()
                if 'h3' in j.extract() or 'h2' in j.extract():
                    subtitle = j_text
                else:
                    for k in j_text.split('\n'):
                        content2subtitle[k] = subtitle
            
            for j in pagedata.xpath(xpath+'/p'):
                if 'br' not in j.extract():
                    continue
                all_line = j.xpath('string(.)')[0].extract()
                for k in all_line.split('\n'):
                    tag_chinese, tag_english, description, link = split_tag_description(k)
                    if description == '':
                        continue
                    # 分开 括号前的中文标签 和 括号中的英文标签，如 异关节目(xenarthran) 
                    if '(' in tag_chinese:
                        tag = tag_chinese.split('(')
                        tag_chinese = tag[0]
                        tag_english = tag[1][:-1]
                    
                    subtitle = content2subtitle[k]
                    list_tag.append({
                        'tag': tag_chinese,
                        'tag_english': tag_english,
                        'description': description,
                        'address': link,
                        'type': [title, subtitle],
                    })                                        
  
    # 其他分站标签
    subsite_args = {
        '英文站': {'page': 12, 'div': 3, 'additional_div': ''},
        '中文站': {'page': 8, 'div': 4, 'additional_div': ''},
        '其他语言分部': {'page': 14, 'div': 5, 'additional_div': ''},
        '被放逐者之图书馆': {'page': 8, 'div': 6, 'additional_div': '/div'}, 
    }
    for key, args in subsite_args.items():
        xpath_nav = f'/html/body/div[1]/div/div[1]/div/div[2]/div[2]/div[4]/div[{args["div"]}]{args["additional_div"]}/ul'
        title = pagedata.xpath(xpath_nav+'/li').xpath('string(.)').extract()

        for t, i in zip(title, range(1, args['page'])):
            xpath = f'/html/body/div[1]/div/div[1]/div/div[2]/div[2]/div[4]/div[{args["div"]}]/div{args["additional_div"]}/div[{i}]'
            content = pagedata.xpath(xpath+'/ul/li')
            
            # 提取 其他语言分部 页面中的子标题 作为标签类型
            if key == '其他语言分部' or (key=='英文站' and t=='体裁与主题'):
                subtitle = ''
                content2subtitle = {}
                for j_selector in pagedata.xpath(xpath+'/*'):
                    j = j_selector.xpath('string(.)').extract_first()
                    if 'h3' in j_selector.extract():
                        subtitle = j
                    else:
                        content2subtitle[j.strip()] = subtitle
            
            for j in content:
                tag_chinese, tag_english, description, link = split_tag_description(j)
                # exclude invalid or found results
                if description == '' or tag_chinese in dict_description.keys():
                    continue
                if key == '其他语言分部':
                    subtitle = content2subtitle[j.xpath('string(.)').extract()[0]]
                    tag_type = [key, t, subtitle]
                elif key == '英文站' and t == '体裁与主题':
                    j = j.xpath('string(.)').extract_first()
                    for k, subtitle in content2subtitle.items():
                        if j in k:
                            tag_type = [key, t, subtitle]
                            break
                else:
                    tag_type = [key, t]
                list_tag.append({
                    'tag': tag_chinese,
                    'tag_english': tag_english,
                    'description': description,
                    'address': link,
                    'type': tag_type,
                }) 

    for i in list_tag:
        i['address'] = strip_address(i['address'])
        for key, value in i.items():
            if value == '':
                i[key] = None

    return list_tag


def get_tag_by_type(
    tag_type: str = '特性',
    json_path: str = '../data/tag.json',
    ) -> set[str]:
    all_tag = load_json(json_path)
    list_tag = []
    for k, v in all_tag.items():
        if tag_type in v['type']:
            list_tag.append(k)
    return set(list_tag)


class Tag(object):
    def __init__(
        self,
        tag_dict: dict,
    ) -> None:
        for k, v in tag_dict.items():
            setattr(self, k, v)
        # tag_english is not specified in the page if same as tag_chinese
        if self.tag_english == '':
            if False not in [i in printable for i in self.tag_chinese]:
                self.tag_english = self.tag_chinese

    def get_dict(self) -> dict:
        return vars(self)

    def __repr__(self) -> str:
        return json.dumps(vars(self), ensure_ascii=False, indent=2)



if __name__ == '__main__':
    list_tag = parse_tag_guide()
    save_json(list_tag, '../data/tag.json')
    # for k, v in dict_description:
        # if k in dict_tag:
