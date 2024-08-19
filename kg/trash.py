# -*- encoding: utf-8 -*-
'''
@File    :   trash.py
@Time    :   2024/07/23 13:56:21
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''


@timeout_decorator.timeout(1)
def load_css_href(
    href: str,
    dir_wikidot: str = DIR_WIKIDOT,
) -> cssutils.css.CSSRuleList:
    css_path = href
    list_rule = []
    if css_path.startswith('../'):
        css_path = dir_wikidot + css_path
        for i in cssutils.parseFile(css_path).cssRules:
            if i.typeString == 'STYLE_RULE':
                list_rule.append(i)
        return list_rule
    else:
        return []


def load_css(
    css_path: str,
    dir_wikidot: str = DIR_WIKIDOT,
) -> cssutils.css.CSSRuleList:
    list_stylerule = []
    for i in cssutils.parseFile(css_path).cssRules:
        if i.typeString == 'STYLE_RULE':
            list_stylerule.append(i)
        # print(j.typeString)
        elif i.typeString == 'IMPORT_RULE':
            css_path: str = i.href
            if css_path.startswith('../'):
                css_path = dir_wikidot + css_path
            else:
                continue
            list_stylerule += load_css(css_path)


def parse_style_tinycss2(
    pagedata: Selector,
    # dir_wikidot: str = DIR_WIKIDOT,
    style_valid: set = set(),
) -> set[str]:
    list_rule = []
    for html_style in xstr(pagedata.css('style'), False):
        for rule in tinycss2.parse_stylesheet(html_style, True, True):
            if rule.type == 'qualified-rule':
                dict_rule = {}
                dict_rule['name'] = ''.join([i.value for i in rule.prelude if hasattr(i, 'value')])
                # print(rule.prelude)
                # print(name)
                dict_rule['decoration'] = {}
                for decoration in tinycss2.parse_blocks_contents(rule.content, True, True):
                    # print(decoration.name, decoration.value)
                    for i in decoration.value:
                        if hasattr(i, 'value') and i.type!='whitespace':
                            dict_rule['decoration'][i.type] = i.value
                    # print(decoration.name, dec_value)
                list_rule.append(dict_rule)
    return list_rule



def get_instruction(
    language: str = 'zh', 
    task: str = 'NER', 
    schema: list[str] | dict = ['人名', '时间', '地点'], 
    example: list[dict] = None,
    input: str = '2010年10月5日\nSite-84\n日本福冈\n蒋渭火博士您好：\n我是冈见亮辅，Site-84神经科学部的3级研究员。他们安排我和你在这个项目上合作。我已经看了你发来的SCP-6009材料，还有你对6009-Catena的形成做出的假设。',
    ) -> list[str]:
    sintructs = []
    split_num = split_num_mapper[task]
    if type(schema) == dict:
        sintruct = json.dumps({'instruction':instruction_mapper[task+language], 'schema':schema, 'input':input}, ensure_ascii=False)
        sintructs.append(sintruct)
    else:
        split_schemas = [schema[i:i+split_num] for i in range(0, len(schema), split_num)]
        for split_schema in split_schemas:
            sintruct = json.dumps({'instruction':instruction_mapper[task+language], 'schema':split_schema, 'input':input}, ensure_ascii=False)
            sintructs.append(sintruct)
    return sintructs


    # task = 'RE'
    # schema = ['被收容于']
    # example = [
    #     {
    #         'input': '乔纳森·哈里斯应被收容于site-122人形收容中心的一个10m x 10m x 10m 的隔间中。收容建筑分为三层，每层三米高。不论何时乔纳森·哈里斯都不应被用其SCP基金会档案编号称呼。乔纳森·哈里斯可被称呼为姜、乔纳森、哈里斯先生、哈里斯、姜·哈里斯、乔纳森·哈里斯或杰克。',
    #         'output': [{"subject": "乔纳森·哈里斯", "object": "site-122"}]
    #     },
    #     {
    #         'input': 'SCP-1948-J应被饲养于███████东北的矿井，定为Site-1948-J。SCP-1948每日应得到食物、水和一包香烟。',
    #         'output': [{"subject": "SCP-1948-J", "object": "Site-1948-J"}]
    #     },
    #     {
    #         'input': '有鉴于SCP-120对基金会的重要性，项目会被全天候处于影像监控及武装守卫的保管之下。任何未被授权的使用都会导致使用者被立即处决。任何人员要使用物品，都必须缴交一份填妥的申请表格（文档#120-23）至设施监督者。',
    #         'output': []
    #     },
    #     {
    #         'input': '科考站点Research Station-05现已建立在SCP-4431-A上方。南极洲各地的地震仪需监测SCP-4431-A的活动，并报告其中的异常现象。在有必要对SCP-4431-A进行调查的情况下，至少应在站点保留一个钻孔探头和一台冰盖钻孔机械。',
    #         'output': [{"subject": "SCP-4431-A", "object": "科考站点Research Station-05"}]
    #     },
    #     {
    #         'input': '进入SCP-2104-B的全部入口都已被金属丝网封锁。封锁边界将由守卫巡逻，防止平民闯入。穿过边界的平民须接受B级记忆删除。\n观察站-04已建立在西班牙██████村，远程监控32个已知的SCP-2104-B入口。',
    #         'output': [{"subject": "SCP-2104-B", "object": "观察站-04"}]
    #     },
    #     {
    #         'input': '一份SCP-2105拷贝应被存放在12号研究所382-C房间的一个安全保险箱内。人员允许在382-C房间内进行SCP-2105的实验，但需要经过一次彻底的心理学检查，在拥有3级安保权限的研究员直接监视下进行试验。所有实验结果需要记录在文件12-2105-C中。',
    #         'output': [{"subject": "SCP-2105", "object": "12号研究所"}]
    #     },
    # ]


    task = 'NER'
    schema = {
        '安保设施': "例如：'Site-33', 'site-cn-71', 'Area-28', 'Area-CN-22', '前哨1699-A', ", 
        '机动特遣队': "例如：'MTF-丁丑-77（“旅行在祂海中的水手们”）', 'MTF Theta-4“园丁”', 'MTF-Omicron-Rho', 'MTF-Gamma-5（“Red Herrings/红鲱鱼”）', '机动特遣队MTF-已酉-7“采菱客”', '机动特遣队Omicron-5（“真爱粉”）', '机动特遣队€-7（螃蟹之王）'",
        }
    example = [
        {
            'input': '乔纳森·哈里斯应被收容于site-122人形收容中心的一个10m x 10m x 10m 的隔间中。收容建筑分为三层，每层三米高。不论何时乔纳森·哈里斯都不应被用其SCP基金会档案编号称呼。乔纳森·哈里斯可被称呼为姜、乔纳森、哈里斯先生、哈里斯、姜·哈里斯、乔纳森·哈里斯或杰克。',
            'output': [{
                "安保设施": ['site-122'], 
                "机动特遣队": [],
                }]
        },
        {
            'input': '所有SCP-1000的媒体报道，都需要审查。所有调查SCP-1000存在性的组织和个人都必须处于MTF ZETA-1000 的监视下，抹杀或施行A级记忆消除。所有物理残留物都必须回收，并保存在基金会，如有必要就用赝品替换。所有声称目击SCP-1000的事件，都必须由MTF ZETA-1000进行调查，即使是微不足道的目击。\n任何接触野生或圈养SCP-1000个体的行为都必须得到Jones主管的批准。任何SCP-1000与人类的接触，包括基金会人员，必须立刻报告Jones主管。',
            'output': [{
                "安保设施": [], 
                "机动特遣队": ['MTF ZETA-1000', 'MTF ZETA-1000'],
                }]
        },
        {
            'input': '科考站点Research Station-05现已建立在SCP-4431-A上方。南极洲各地的地震仪需监测SCP-4431-A的活动，并报告其中的异常现象。在有必要对SCP-4431-A进行调查的情况下，至少应在站点保留一个钻孔探头和一台冰盖钻孔机械。\n应与南极洲所有的基金会和非基金会科考站点保持联系，以获取有关SCP-4431-B显现的报告。如果报告了显现事件的话，建议站点人员监控该次显现以及由此产生的SCP-4431-C实体。死亡实体留下的物品需送至最近的基金会设施。如有必要，应部署机动特遣队Xi-1（“米斯卡塔尼克急件Dispatch from Miskatonic”）进行收容。目击到这些异常的非基金会人员将接受合适的记忆删除并离开南极洲。',
            'output': [{
                "安保设施": ['科考站点Research Station-05'], 
                "机动特遣队": ['机动特遣队Xi-1（“米斯卡塔尼克急件Dispatch from Miskatonic”）'],
                }]
        },

        {
            'input': '如信息真实性被确认，应派遣机动特遣队MTF-△-09（“树栖者”）对SCP-CN-2375样本进行回收并存储于A01-28低温组织储存库中。若回收过程中项目外壁破损致使内部组织暴露，需使用氧-乙炔高温焚化炉将其生物组织灭活，残余物需按基金会标准生化废物处理方案丢弃。\nSCP-CN-2375的相关收容与研究工作交由Site-CN-09生物部负责。',
            'output': [{
                "安保设施": ['Site-CN-09'], 
                "机动特遣队": ['机动特遣队MTF-△-09（“树栖者”）'],
                }]
        },
        {
            'input': '所有新出现的SCP-CN-2362-1均需被立即控制并适当地收容；为此，Site-CN-25内应始终存有至少50%的空置收容单元，以保证对新出现SCP-CN-2362-1的收容功能。MTF-庚子-5（“刺杀一群想法”）将常驻该站点，以在紧急情况下压制敌意实体，并允许不经上报使用致命武力。',
            'output': [{
                "安保设施": ['Site-CN-25'], 
                "机动特遣队": ['MTF-庚子-5（“刺杀一群想法”）'],
                }]
        },
    ]