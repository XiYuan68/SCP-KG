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

from oneke import get_instruction, get_response
    

def load_scp(json_scp: str = '../data/scp.json') -> list[dict]:
    with open(json_scp) as f:
        return json.load(f)


SCHEMA_EXAMPLE_NER = {
    '安保设施': {
        'schema': "例如：'Site-33', 'site-cn-71', 'Area-28', 'Area-CN-22', '前哨1699-A', ",
        'example': [
            {
                'input': 'site-122人形收容中心的一个10m x 10m x 10m 的隔间中。',
                'output': ['site-122']
            },
            {
                'input': '科考站点Research Station-05现已建立在SCP-4431-A上方。',
                'output': ['科考站点Research Station-05'], 
            },
            {
                'input': 'Site-CN-09生物部负责。',
                'output': ['Site-CN-09'],
            },
            {
                'input': 'Site-CN-25内应始终存有至少50%的空置收容单元，',
                'output': ['Site-CN-25'], 
            },
            {
                'input': '前哨站CN-21已于项目中心南面21千米处建立以执行消极收容措施。',
                'output': ['前哨站CN-21']
            },
            {
                'input': 'Area-CN-07的仓库中。',
                'output': ['Area-CN-07'], 
            },
            {
                'input': 'Area-12中节肢动物翼区的特制水生动物收容间中，',
                'output': ['Area-12'], 
            },
            {
                'input': '前哨1699-A已围绕SCP-1699建立，',
                'output': ['前哨1699-A'], 
            },
            {
                'input': 'MTF Beta-4 (\"Castaways\"-落难) 合作运往 Site-64 收容。',
                'output': ['Site-64'], 
            },
        ]
    }, 
    '机动特遣队': {
        'schema': "例如：'MTF-丁丑-77（“旅行在祂海中的水手们”）', 'MTF Theta-4“园丁”', 'MTF-Omicron-Rho', 'MTF-Gamma-5（“Red Herrings/红鲱鱼”）', '机动特遣队MTF-已酉-7“采菱客”', '机动特遣队Omicron-5（“真爱粉”）', '机动特遣队€-7（螃蟹之王）'",
        'example':[
            {
                'input': 'MTF ZETA-1000 的监视下，',
                'output': ['MTF ZETA-1000'],
            },
            {
                'input': '机动特遣队Xi-1（“米斯卡塔尼克急件Dispatch from Miskatonic”）进行收容。',
                'output': ['机动特遣队Xi-1（“米斯卡塔尼克急件Dispatch from Miskatonic”）'],
            },
            {
                'input': '机动特遣队MTF-△-09（“树栖者”）对SCP-CN-2375样本进行回收并存储于A01-28低温组织储存库中。',
                'output': ['机动特遣队MTF-△-09（“树栖者”）'],
            },
            {
                'input': 'MTF-庚子-5（“刺杀一群想法”）将常驻该站点，',
                'output': ['MTF-庚子-5（“刺杀一群想法”）'],
            },
            {
                'input': 'MTF U-58只可录用Cohen-Weinberg共情评分中得分-65以下、且坚持严格的反集体主义道德观及价值观的人员。',
                'output': ['MTF U-58'],
            },
            {
                'input': '机动特遣队无法压制[数据丢失]时，',
                'output': [],
            },
            {
                'input': 'MTF Beta-4 (\"Castaways\"-落难) 合作运往 Site-64 收容。',
                'output': ['MTF Beta-4 (\"Castaways\"-落难)'],
            },
        ]
    }
}


SCHEMA_EXAMPLE_RE = {
    '被收容于的安保设施':{
        'schema': '这个关系类型用来表示一个基金会项目被收容于一个安保设施的关系。安保设施特指包含“site”，“area”，“outpost”字样的地点。基金会项目是主体，安保设施是客体。',
        'example': [
            {
                'input': 'SCP-001-J目前保管于Site-00，该区具体位置必须绝对保密。因此，Site-00完全由自动防御系统把守，不允许有任何人类员工。',
                'output': [{"subject": "SCP-001-J", "object": "Site-00"}]
            },
            {
                'input': 'ATF Ru-199负责监测当地居民是否看到SCP-4840。声称看到过SCP-4840的个体将被押送至Site-210进行处理。',
                'output': []
            },
            {
                'input': 'SCP-055-DE-J保存在SITE-DE19的食堂里谁都看得到！这东西尝起来是真好吃！',
                'output': [{"subject": "SCP-055-DE-J", "object": "SITE-DE19"}]
            },
            {
                'input': '仅存的一个SCP-CN-2068实体被收容于Area-CN-22的低风险物品收容单元内。实验-21后，制定以下收容措施。',
                'output': [{"subject": "SCP-CN-2068", "object": "Area-CN-22"}]
            },
            {
                'input': 'SCP-3103被收容在Site-██的标准收容室的一个鸟笼中，需与其他标本隔离。',
                'output': []
            },
            {
                'input': 'Outpost-618已建立以用于秘密收容SCP-1295。特工与研究员都伪装为工作人员，顾客和当地执法人员，并阻止平民与SCP-1295进行交流。',
                'output': [{"subject": "SCP-1295", "object": "Outpost-618"}]
            },
        ]
    }
}


def get_schema_ner(
    schema_example_ner: dict = SCHEMA_EXAMPLE_NER,
    entity: list[str] = None,
) -> dict:
    if entity is None:
        entity = schema_example_ner.keys()
    schema = dict((i, schema_example_ner[i]['schema']) for i in entity)
    return schema


def get_example_ner(
    schema_example_ner: dict = SCHEMA_EXAMPLE_NER,
    entity: list[str] = None,
) -> list[dict]:
    if entity is None:
        entity = schema_example_ner.keys()
    example = []
    example_input = []
    for e in entity:
        list_example_e = schema_example_ner[e]['example']
        for example_e in list_example_e:
            output_dict = {}
            for i in entity:
                if i != e:
                    output_dict[i] = []
                else:
                    output_dict[i] = example_e['output']
            input = example_e['input']
            if input not in example_input:
                example.append({'input': input, 'output':output_dict})
                example_input.append(input)
            else:
                idx = example_input.index(input)
                example[idx]['output'][e] = example_e['output']
    return example


def ner(
    input: str,
    schema: dict,
    example: list[dict],
) -> dict:
    sintruct = get_instruction(task="NER", schema=schema, example=example, input=input)
    response =  get_response(sintruct)
    output = json.loads(response)
    return output


if __name__ == '__main__':
    list_scp = load_scp()
    scp = list_scp[97]
    special_containment_procedure = scp['special_containment_procedure']
    # task = 'NER'
    # entity = ['安保设施']
    # 无法正确抽取安保设施，猜测因为训练数据中不存在，需要进行实体抽取微调
    task = 'RE'
    entity = ['被收容于的安保设施']
    schema_example = SCHEMA_EXAMPLE_RE
    schema = get_schema_ner(
        schema_example_ner=schema_example,
        entity=entity,
    )
    example = get_example_ner(
        schema_example_ner=schema_example,
        entity=entity,
    )
    sintruct = get_instruction(task=task, schema=schema, example=example, 
        input=special_containment_procedure)
    reponse =  get_response(sintruct)
    print(reponse)

