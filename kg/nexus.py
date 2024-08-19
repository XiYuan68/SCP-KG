# -*- encoding: utf-8 -*-
'''
@File    :   nexus.py
@Time    :   2024/07/17 02:13:46
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

from utilities import DIR_WIKIDOT


if __name__ == '__main__':
    html_file = DIR_WIKIDOT + 'nexus-series'