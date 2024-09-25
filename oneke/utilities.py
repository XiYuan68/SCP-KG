# -*- encoding: utf-8 -*-
'''
@File    :   utilities.py
@Time    :   2024/08/29 15:18:12
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

import json
import re
from string import printable

from urllib.parse import unquote
from scrapy import Selector
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_json(json_path: str):
    with open(json_path) as f:
        return json.load(f)
    

CSS_REMOVE = [
    'div[style="display: none"]',
    'div[style="display: none;"]',
    'div.code',
    'div.pseudocrumbs',
    'div.adytoc',
    'div#u-credit-view',
    'div.page-rate-widget-box', 
    'div.creditRate', 
    'div.licensebox',
    'div.info-container',
    'div.footer-wikiwalk-nav',
    'div.footnotes-footer',
    # 'div#breadcrumbs',
    'script',
    'div.scp-image-block',
    'div.scp-image-caption',
    'div.image-box',
    'span.fnnum',
    'span.footnoteref',
    'sup.footnoteref',
    'span.fncon',
    'span.lang-tr',
    'style',
    'div#counter',
    # TODO: include text with line-through
    'span[style="text-decoration: line-through;"]',
    'span[style="text-decoration: line-through"]',
]

def get_page_text(html_path: str) -> str:
    with open(html_path) as f:
        page = Selector(text=f.read()).css('div#page-content')

    all_content_text = page.extract_first()
    if all_content_text is None:
        return ''
    for i in CSS_REMOVE:
        for j in page.css(i).extract():
            all_content_text = all_content_text.replace(j, '')
    text = xstr(Selector(text=all_content_text))
    return text


QUOTE_START = ('“', '「', '[', '【', '{', '‘', '<', '《', '(', '（', '"')
QUOTE_END = ('”', '」', ']', '】', '}', '’', '>', '》', ')', '）', '"')
DICT_QUOTE = dict([(s, e) for s, e in zip(QUOTE_START, QUOTE_END)])
SENTENCE_END = set('。！？')

def split_sentence(paragraph: str|None) -> list[str]:
    if paragraph is None:
        return []
    list_sentence = []
    # 以 SENTENCE_END 分割句子
    for j in paragraph.split('\n'):
        j = j.strip()
        if j == '':
            continue

        has_end = [k in j for k in SENTENCE_END]
        if True not in has_end:
            list_sentence.append(j)
        else:
            text_splitted = []
            sentence = ''
            len_j = len(j)
            quote_end_unfinished = []
            for idx, k in enumerate(j):
                # 最后一个字符
                if idx == len_j - 1:
                    sentence += k
                    text_splitted.append(sentence)
                # 句子继续
                elif k not in SENTENCE_END:
                    sentence += k
                    if k in QUOTE_START :
                        quote_end_unfinished.append(DICT_QUOTE[k])
                    elif k in QUOTE_END:
                        if k in quote_end_unfinished:
                            quote_end_unfinished.remove(k)
                # k in SENTENCE_END
                else:
                    sentence += k
                    # 句子结束
                    if len(quote_end_unfinished)==0 and j[idx+1] not in SENTENCE_END:
                        text_splitted.append(sentence)
                        sentence = ''
            try:
                for k in QUOTE_END:
                    if text_splitted[-1] == k:
                        text_splitted[-2] += k
                        text_splitted.pop(-1)
                        break
            except Exception:
                pass
            list_sentence += text_splitted
    return list_sentence


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


def strip_unprintable(sentence: str) -> list[str]:
    sublist_printable = []
    word = ''
    for char in sentence:
        if char in printable:
            word += char
        else:
            if word != '':
                sublist_printable.append(word.strip())
            word = ''
    if word != '':
        sublist_printable.append(word.strip())
    return sublist_printable


def sentence_has_printable(list_sentence: list[str]) -> list[dict]:
    list_dict = []
    for sentence in list_sentence:
        d = {}
        sublist_printable = strip_unprintable(sentence)
        if len(sublist_printable) > 0:
            d['word'] = sublist_printable
            d['sentence'] = sentence
            list_dict.append(d)
    return list_dict


# def load_model(
#     model_path: str,
#     lora_path: str = None,
# ) -> 