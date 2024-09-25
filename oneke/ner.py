# -*- encoding: utf-8 -*-
'''
@File    :   prepare_data.py
@Time    :   2024/08/29 15:17:25
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

import re
from copy import deepcopy
import json
import os
import random
import subprocess
import time

from joblib import Parallel, delayed
from opencc import OpenCC
chinese_converter = OpenCC('t2s')
import pandas as pd

from utilities import load_json, split_sentence, save_json, get_page_text


ENTITY_PATTERN = {
    'SCP基金会项目': re.compile(r'scp(?:-[a-zA-Z]+)?-[0-9]+(?:-[a-zA-Z]{2,}){0,2}(?:-j)?(?:-[0-9])?', re.I)
}
DIR_WIKIDOT = '../SCP-CN/scp-wiki-cn.wikidot.com/'



def get_sample_dict(
    sentence: str,
    entity_type: str,
    entity_found: list[str]|str,
) -> dict:
    if isinstance(entity_found, str):
        entity_found = [entity_found]
    d = {
        'text': sentence,
        'entity': [{"entity": i, "entity_type": entity_type} for i in entity_found]
    }
    return d    


def ner_single(
    sentence: str,
    entity: str,
    func = None
) -> dict:
    pattern = ENTITY_PATTERN[entity]
    list_match = re.findall(pattern, sentence)
    if func is not None:
        list_match = func(list_match)
    d = {
        'text': sentence,
        'entity': [{"entity": i, "entity_type": entity} for i in list_match]
    }
    return d


def ner(
    list_scp_dict: list[dict],
    entity: str,
) -> list[dict]:
    list_sentence = []
    for dict_scp in list_scp_dict:
        list_sentence += split_sentence(dict_scp['special_containment_procedure'])
        list_sentence += split_sentence(dict_scp['description'])
    args = [(i, entity) for i in list_sentence]
    pool = Parallel(-1)
    result = pool(delayed(ner_single)(*i) for i in args)
    return result


def scp(
    json_scp: str = '../data/scp.json',
    pattern: str = r'scp(?:-[a-z]+)?[-‑－\s]?[0-9]+(?:[-‑－][a-z]{2,}){0,2}(?:[-‑－]j)?(?:[-‑－][0-9])?',
) -> list[dict]:
    pattern = re.compile(pattern, re.I)
    list_scp_dict = load_json(json_scp)
    list_sentence = []
    for dict_scp in list_scp_dict:
        list_sentence += split_sentence(dict_scp['special_containment_procedure'])
        list_sentence += split_sentence(dict_scp['description'])
    list_sample = []
    list_sentence = list(set(list_sentence))
    for sentence in list_sentence:
        list_match = re.findall(pattern, sentence)
        if len(list_match) > 0:
            sample = get_sample_dict(sentence, 'SCP基金会项目', list_match)
            list_sample.append(sample)
    return list_sample

# TODO：英译中 site-站点，area-区域，outpost-前哨站 的匹配
facility_prefix_cn = [
    '武装', '生物性', '生化', '收容', '维度性', '人形生物', '特外', '外太阳系', '月面', 
    '受保护', '临时', '圣物', '圣遗物', '研究', '储藏', '监察', '移动', '测试', '历史',
    '生物', '观察', '前哨', '人形', '时间', '存储', '指挥', '附属', '概念', '安保',
    '模因', '异常动物学'
]
facility_prefix_en = [
    'Armed', 'Biological', 'Containment', 'Dimensional', 'Humanoid', 'Exclusionary',
    'Extrasolar', 'Lunar', 'Protected', 'Provisional', 'Reliquary', 'Research', 
    'Storage', 'Surveillance', 'Mobile', 'Bio', 'Sat', 'remote', 'resource',
    'Parazoology'
]
facility_suffix_cn = [
    '站点', '区域', '前哨', '哨所', 
    '区', '站', '哨',
]
facility_suffix_en = [
    'Site', 'Area', 'Outpost', r'Observation[-\s]Post'
]
digit = r'[0-9]+'
letter = r'[a-zα-ωΑ-Ω]+'
digit_letter = r'[0-9a-zα-ωΑ-Ω]+'
def modify_pattern(
    pattern: str,
    optional: bool = True,
    before: str = r'[-\s]',
) -> str:
    pattern = r'(?:' + before + pattern + ')'
    if optional:
        pattern += '?'
    return pattern
    
def facility_from_sentence(sentence: str) -> dict | None:
    list_suffix = []
    pattern = '|'.join(facility_suffix_en + facility_suffix_cn)
    list_suffix = re.findall(pattern, sentence, re.I)
    if len(list_suffix) == 0:
        return None
    list_suffix_new = []
    for i in list_suffix:
        list_suffix_new.append(i)
        if len(i) == 1:
            for j in list_suffix:
                if i in j and len(j) > 1:
                    list_suffix_new.pop(-1)
                    break
    list_suffix = list_suffix_new

    # Site-CN-85-D, Site-DE15, Site-M1, Site-Ω1
    pattern_en = modify_pattern(letter)
    # Site-168, Site 51, Site-64K
    pattern_en += modify_pattern(digit_letter, optional=False)
    # Site-04-a, Site-1483-Alpha
    pattern_en += modify_pattern(digit_letter, before=r'[-]')

    list_found = []
    for suffix in list_suffix:
        if suffix in facility_suffix_cn:
            list_prefix = deepcopy(facility_prefix_cn)
        else:
            list_prefix = deepcopy(facility_prefix_en)
            
        len_suffix_previous = 0
        while len_suffix_previous != len(suffix):
            len_suffix_previous = len(suffix)
            for prefix in list_prefix:
                pattern = prefix + r'[-\s&(?:and)]*' + suffix
                list_found = re.findall(pattern, sentence, re.I)
                if len(list_found) > 0:
                    suffix = list_found[0]
                    list_prefix.remove(prefix)
        # 回收区-1, 武装地形学区-7
        if len(suffix) == 1:
            continue
        # example: 
        if suffix in facility_suffix_en:
            # pattern = suffix + r'[-\s]?[a-z]*[-\s]?[0-9]+(?:[-\s][0-9]+)?[-\s][a-z]*'
            pattern = suffix + pattern_en
        # 避免“在目击发生事件的区域500米内发生了相同事件”中“区域500”被识别为实体
        else:
            pattern = suffix + r'[-\s][0-9]+(?:[-\s][a-z]+)?(?:[-\s][0-9]+)?(?:[-\s][a-z]+)?'
        list_found += re.findall(pattern, sentence, re.I)
    list_found = list(set(list_found))
    if len(list_found) > 0:
        sample = get_sample_dict(sentence, 'SCP基金会安保设施', list_found)
        return sample
    return None


def sentence_from_address(
    address: str,
    dir_wikidot: str = DIR_WIKIDOT,
) -> list[str]:
    html_path = dir_wikidot + address + '.html'
    text = get_page_text(html_path)
    list_sentence = split_sentence(text)
    return list_sentence


def facility_from_guide(
    json_sentence: str = 'data/ner/facility.sentence.json',
    json_facility: str = '../data/facility.json',
    dir_wikidot: str = DIR_WIKIDOT,
    updata_sentence: bool = False,
) -> list[dict]:
    try:
        assert updata_sentence == False
        list_sentence = load_json(json_sentence)
        assert len(list_sentence) > 0
    except Exception:
        list_facility_dict = load_json(json_facility)
        list_address = []
        for dict_facility in list_facility_dict:
            for i in ['object_related', 'object_contained', 'incident']:
                list_address += dict_facility[i]
        list_address = set(list_address)
        pool = Parallel(n_jobs=-1)
        list_result = pool(delayed(sentence_from_address)(*(i, dir_wikidot)) for i in list_address)
        list_sentence = []
        for i in list_result:
            list_sentence += i
        list_sentence = list(set(list_sentence))
        jsons_list_sentence = json.dumps(
            list_sentence, ensure_ascii=False, indent=2)
        jsons_list_sentence = chinese_converter.convert(jsons_list_sentence)
        with open(json_sentence, 'w') as f:
            f.write(jsons_list_sentence)
    pool = Parallel(n_jobs=-1)
    list_result = pool(delayed(facility_from_sentence)(i) for i in list_sentence)
    list_sample = [i for i in list_result if i is not None]
    return list_sample


def get_pattern_quote(quote: str = '\(\)') -> str:
    left = quote[:(len(quote)//2)]
    right = quote[-(len(quote)//2):]
    pattern = r'(?:' + left + r'[^' +left+right+r']+' + right + r')'
    return pattern


def get_pattern_select(
    list_pattern: list[str],
    optional: bool = False,
    func = None,
) -> str:
    if func is not None:
        list_pattern = [func(i) for i in list_pattern]
    pattern = r'(?:' + '|'.join(list_pattern) + ')'
    if optional:
        pattern += '?'
    return pattern


def connect_pattern(list_pattern: list[str]) -> str:
    pattern = r'[-\s]?'.join(list_pattern)
    return pattern




def taskforce_from_guide(
    json_sentence: str = 'data/ner/taskforce.sentence.json',
    json_taskforce = '../data/taskforce.json',
    dir_wikidot: str = DIR_WIKIDOT,
    updata_sentence: bool = False,
) -> list[dict]:
    try:
        assert updata_sentence == False
        dict_sentence = load_json(json_sentence)
        list_sentence = dict_sentence['sentence']
        list_name = dict_sentence['name']
        assert len(list_sentence) > 0        

    except Exception:
        list_taskforce_dict = load_json(json_taskforce)
        list_address = []
        list_name = []
        for dict_taskforce in list_taskforce_dict:
            name: str = dict_taskforce['name']
            if '特遣队' in name:
                name = re.sub(r'.*特遣队', '', name)
            elif 'MTF' in name:
                name = re.sub(r'mtf-?', '', name, flags=re.I)
            name = name.replace(' ', '-')
            list_name.append(name)
            for i in ['object_utilized', 'object_contained', 'action_report']:
                list_address += dict_taskforce[i]

        list_sentence: list[dict] = []
        for address in list_address:
            html_path = dir_wikidot + address + '.html'
            text = get_page_text(html_path)
            list_sentence += split_sentence(text)
        list_sentence = list(set(list_sentence))
        dict_sentence = {'name': list_name, 'sentence': list_sentence}
        sdict_sentence = json.dumps(dict_sentence, ensure_ascii=False)
        sdict_sentence = chinese_converter.convert(sdict_sentence)
        dict_sentence = json.loads(sdict_sentence)
        save_json(dict_sentence, json_sentence)

    list_name = [i.replace('-', '[-\s]?') for i in list_name]
    tf_code_en = [
        'Alpha', 'Beta', 'Chi', 'Delta', 'ETA', 'Epsilon', 'Eta', 'Gamma', 'Iota',
        'Kappa', 'Lambda', 'Mu', 'Nu', 'Omicron', 'Phi', 'Pi', 'Psi', 'Rho', 
        'Sigma', 'Stigma', 'Tau', 'Theta', 'Upsilon', 'Xi', 'Zeta',
    ]
    # all greek letters
    tf_code_en += [chr(code) for code in range(0x391, 0x3A2)]
    tf_code_en += [chr(code) for code in range(0x3A3, 0x3AA)]
    tf_code_en += [chr(code) for code in range(0x3B1, 0x3CA)]
    list_name_maybe = [i+r'[-\s]?[0-9]+' for i in tf_code_en]
    tf_code_cn_head = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    tf_code_cn_tail = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    tf_code_cn = []
    for i in tf_code_cn_head:
        for j in tf_code_cn_tail:
            tf_code_cn.append(i + j)
    list_name_maybe += [i+r'[-\s]?[0-9]+' for i in tf_code_cn]
    
    # func: avoiding 机动特遣队Omega-144 being extracted as 机动特遣队Omega-1
    pattern_official_mtf = get_pattern_select(
        list_name,
        func = lambda x: x + r'[0-9]*')
    pattern_any_mtf = get_pattern_select(
        list_name+list_name_maybe,
        func = lambda x: x + r'[0-9]*')

    suffix_tf_cn = get_pattern_select(['机动', '联合', '应用', '混合', '协作'])
    profix_tf_cn = get_pattern_select(['特遣', '机动', '部', '小'])
    tf_cn = '队'
    suffix_tf_en = get_pattern_select(['m','r','s','a','c','o','t','j','p'])
    tf_en = 'tf'
    suffix_tf_en_full = get_pattern_select(['Mobile', 'Applied', r'Armed\sMobile'])
    tf_en_full = r'Task[-\s]?Force'

    list_quote = [r'\(\)', r'（）', r'“”',r'‘’', r'\"\"', r'\'\'', r'「」']
    list_pattern_quote = [get_pattern_quote(i) for i in list_quote]
    quote = '(?:' + '|'.join(list_pattern_quote) + ')?'


    list_sample = []
    for sentence in list_sentence:
        # ignore sentences without any MTF name
        name_found = re.findall(pattern_any_mtf, sentence, re.I)
        list_match: list[str] = []
        for name in name_found:

            # 机动特遣队 Nu-3 (湖泊恐惧症-\"Limnophobia\"), 特遣队Lambda-5
            cn_found = re.findall(connect_pattern([tf_cn, name]), sentence, re.I)
            if len(cn_found) > 0:
                cn_found = get_pattern_select(cn_found)
                list_match += re.findall(profix_tf_cn+r'[-\s]?'+cn_found, sentence, re.I)
                for match in list_match:
                    pattern = connect_pattern([suffix_tf_cn, match, quote])
                    list_match += re.findall(pattern, sentence, re.I)
            
            # MTF Alpha-4（“小马快递”）", STF Rho-7（“问候派对”）
            en_found = re.findall(tf_en+r'[-\s]?'+name, sentence, re.I)
            if len(en_found) > 0:
                en_found = get_pattern_select(en_found)
                pattern = connect_pattern([suffix_tf_en, en_found, quote])
                list_match += re.findall(pattern, sentence, re.I)

            # Mobile Task Force Epsilon-11 (\"Nine-Tailed Fox\")
            en_full_found = re.findall(tf_en_full+r'[-\s]?'+name, sentence, re.I)
            if len(en_full_found) > 0:
                en_full_found = get_pattern_select(en_full_found)
                pattern = connect_pattern([suffix_tf_en_full, en_full_found, quote])
                list_match += re.findall(pattern, sentence, re.I)
            
            # no MTF or 机动特遣队 before taskforce name
            # Alpha-4（“被放逐者之图书馆”）", Eta-10, 己未-05“博弈尘埃”
            if len(list_match) == 0:
                # only select official mtf names
                if len(re.findall(pattern_official_mtf, name, re.I)) > 0:
                    pattern = connect_pattern([name, quote])
                    list_match += re.findall(pattern, sentence, re.I)

        # ignore "MTF-庚午-01-" from MTF-庚午-01-016：你们的送货车开进来的时候
        list_match = [i for i in list_match if i[-1]!='-']

        if len(list_match) > 0:
            list_match = [i.strip() for i in list_match]
            # ignore substrings in matches
            list_match_new = []
            for i in list_match:
                # 
                is_substring = False
                for j in list_match:
                    if i in j and i != j:
                        is_substring = True
                if not is_substring:
                    list_match_new.append(i)
            list_match = list_match_new
            sample = get_sample_dict(sentence, 'SCP基金会机动特遣队', list_match)
            list_sample.append(sample)
    return list_sample


def entity_from_sample(list_sample: list[dict]) -> list[str]:
    entity = set()
    for i in list_sample:
        for j in i['entity']:
            entity.add(j['entity']) 
    entity = list(entity)
    entity.sort()
    return entity



def combine_sample(
    list_json_each_entity: list[str] = [
        'data/ner/scp.json',
        'data/ner/facility.json',
        'data/ner/taskforce.json',
    ],
    n_sample: int = 5000,
    json_sample: str = 'data/ner/sample.json',
) -> list[dict]:

    entity_type_index = ['SCP基金会机动特遣队', 'SCP基金会安保设施', 'SCP基金会项目']
    entity_type_index = dict([(i, idx) for idx, i in enumerate(entity_type_index)])

    dict_sentence = {}
    dict_entity = {}
    for i in list_json_each_entity:
        list_sample = load_json(i) 
        for sample in list_sample:
            sentence = sample['text']
            list_entity = sample['entity']
            if sentence not in dict_sentence.keys():
                dict_sentence[sentence] = {
                    'entity': [], 
                    'entity_type': [], 
                    'entity_type_index': [], 
                    'entity_type_count': 0}
            dict_sentence[sentence]['entity'] += [i['entity'] for i in list_entity]
            dict_sentence[sentence]['entity_type'] += [i['entity_type'] for i in list_entity]
            dict_sentence[sentence]['entity_type_index'] += [entity_type_index[i['entity_type']] for i in list_entity]
            dict_sentence[sentence]['entity_type_count'] += 1
            for entity in list_entity:
                text = entity['entity']
                entity_type = entity['entity_type']
                if text not in dict_entity.keys():
                    dict_entity[text] = {'type': entity_type, 'count': 0}
                dict_entity[text]['count'] += 1
    
    df_sentence = pd.DataFrame([{
        'sentence': k, 
        'entity': v['entity'],
        'entity_type': v['entity_type'],
        'entity_type_index': v['entity_type_index'],
        'entity_type_count': v['entity_type_count'],
    } for k, v in dict_sentence.items()])
    df_sentence['entity_frequency'] = df_sentence['entity'].apply(lambda x: max([dict_entity[i]['count'] for i in x]))
    df_sentence['entity_count'] = df_sentence['entity'].apply(lambda x: len(x))
    df_sentence['entity_type_index'] = df_sentence['entity_type_index'].apply(lambda x: min(x))
    df_sentence['entity_length'] = df_sentence['entity'].apply(lambda x: max([len(i) for i in x]))
    
    # more #type_of_entity -> lower entity_frequency -> 
    # more #entity -> entity_type (MTF-facility-SCP) -> less entity_length
    df_sentence.sort_values(
        by = [
            'entity_type_count', 'entity_frequency', 'entity_count', 
            'entity_type_index', 'entity_length',
        ],
        ascending = [False, True, False, True, True],
        inplace = True)
    # df_sentence.iloc[:50]
    
    list_sample = []
    for i in range(n_sample):
        row = df_sentence.iloc[i]
        list_entity = []
        for e, t in zip(row['entity'], row['entity_type']):
            list_entity.append({'entity': e, 'entity_type': t})
        sample = {'text': row['sentence'], 'entity': list_entity}
        list_sample.append(sample)
    
    save_json(list_sample, json_sample)


def convert_sample(
    json_sample: str = 'data/ner/sample.json',
    josn_train: str = 'data/ner/train.json',
    josn_test: str = 'data/ner/test.json',
    json_schema: str = 'data/ner/schema.json',
    test_split: float = 0.05,
    random_seed: int = 2024,
) -> tuple[str]:

    schema = ['SCP基金会机动特遣队', 'SCP基金会安保设施', 'SCP基金会项目']
    schema = json.dumps(schema, ensure_ascii=False) + '\n[]\n{}'
    with open(json_schema, 'w') as f:
        f.write(schema)

    list_sample = load_json(json_sample)
    n_sample = len(list_sample)
    n_test = int(n_sample * test_split)
    random.seed(random_seed)
    random.shuffle(list_sample)

    json_train_temp = josn_train + '.tmp'
    list_sample_train = []
    for i in list_sample[:-n_test]:
        list_sample_train.append(json.dumps(i, ensure_ascii=False)+'\n')
    with open(json_train_temp, 'w') as f:
        f.writelines(list_sample_train)
    command = f'''
python InstructKGC/ie2instruction/convert_func.py \
--src_path {json_train_temp} \
--tgt_path {josn_train} \
--schema_path {json_schema} \
--language zh \
--task NER \
--split_num 6 \
--random_sort \
--split train
'''
    output_train = os.popen(command)

    json_test_temp = josn_test + '.tmp'
    list_sample_test = []
    for i in list_sample[-n_test:]:
        list_sample_test.append(json.dumps(i, ensure_ascii=False)+'\n')
    with open(json_test_temp, 'w') as f:
        f.writelines(list_sample_test)
    command = f'''
python InstructKGC/ie2instruction/convert_func.py \
--src_path {json_test_temp} \
--tgt_path {josn_test} \
--schema_path {json_schema} \
--language zh \
--task NER \
--split_num 6 \
--random_sort \
--split test
'''
    output_test = os.popen(command)

    # os.remove(json_train_temp)
    # os.remove(json_test_temp)
    return output_train, output_test


def train_lora(
    josn_train: str = 'data/ner/train.json',
    output_dir: str = 'model/ner/',
    model_path: str = '../../LLM/OneKE/',
    # batch size set for one 22G 2080Ti
    batch_size: int = 16,
    epoch: int = 3,
    val_size: int = 100,
    save_steps: int = 25,
    eval_steps: int = 100,
) -> None:
    command = [
        'torchrun', '--master_port=1287', 'InstructKGC/src/finetune.py', 
        '--do_train', '--do_eval', '--overwrite_output_dir', '--model_name_or_path', 
        model_path, '--stage', 'sft', '--model_name', 'llama', 
        '--template', 'llama2_zh', '--train_file', josn_train, 
        '--val_set_size', val_size, '--output_dir', output_dir, 
        '--per_device_train_batch_size', batch_size, 
        '--per_device_eval_batch_size', batch_size, 
        '--gradient_accumulation_steps', '1', '--preprocessing_num_workers', '16', 
        '--num_train_epochs', epoch, '--learning_rate', '5e-5', 
        '--max_grad_norm', '0.5', '--optim', '"adamw_torch"', 
        '--max_source_length', '400', '--cutoff_len', '700', 
        '--max_target_length', '300', '--evaluation_strategy', '"steps"', 
        '--eval_steps', eval_steps, '--save_strategy', '"steps"', 
        '--save_steps', save_steps, '--save_total_limit', '10', 
        '--lora_r', '64', '--lora_alpha', '64', '--lora_dropout', '0.05', 
        '--bf16', '--bits', '4'
    ]
    subprocess.run(command)



# https://github.com/zjunlp/DeepKE/blob/main/example/llm/InstructKGC/README_CN.md#611%E5%9F%BA%E7%A1%80%E6%A8%A1%E5%9E%8Blora
# {'total': {'总样本数': 250, '错误数': 0, 'P': 92.68, 'R': 96.2, 'F1': 94.41}}
# Time Elapsed: 1818.35 seconds
def test_lora(
    dir_model: str = '../../LLM/OneKE/',
    dir_checkpoint: str = 'model/ner/checkpoint-700/',
    json_input: str = 'data/ner/test.json',
    json_output: str = None,
) -> None:
    with open(json_input) as f:
        n_sample = len(f.readlines())
    print(f'Testing LoRa model on {n_sample} samples')
    time_start = time.time()

    if json_output is None:
        json_output = dir_checkpoint + 'test_result.json'
    command = [
        'python', 'InstructKGC/src/inference.py', '--stage', 'sft',
        '--model_name_or_path', dir_model, '--checkpoint_dir', dir_checkpoint,
        '--model_name', 'llama', '--template', 'llama2', '--do_predict', '--input_file',
        json_input, '--output_file', json_output, '--finetuning_type', 'lora',
        '--output_dir', 'lora/test', '--predict_with_generate', 
        '--cutoff_len', '512', '--bf16', '--max_new_tokens', '300', '--bits', '4',
    ]
    subprocess.run(command)

    time_stop = time.time()
    print('Time Elapsed: %.2f seconds'%(time_stop - time_start))

    command = [
    'python',
    'InstructKGC/ie2instruction/eval_func.py',
    '--path1',
    json_output,
    '--task',
    'NER',
    ]
    subprocess.run(command)



if __name__ == '__main__':
    # list_sample = scp()
    # save_json(list_sample, 'data/ner/scp.json')
    # print(len(list_sample))
    # entity = entity_from_sample(list_sample)
    # save_json(entity, 'data/ner/scp.enity.json')
    # print(len(entity))

    # json_taskforce = '../data/taskforce.json'
    # dir_wikidot: str = DIR_WIKIDOT
    # list_sample = facility_from_guide(updata_sentence=False)
    # list_sample = taskforce_from_guide(updata_sentence=False)
    # print(len(list_sample))
    # save_json(list_sample, 'data/ner/taskforce.json')
    # entity = entity_from_sample(list_sample)
    # save_json(entity, 'data/ner/taskforce.enity.json')
    # print(len(entity))
    
    # combine_sample(n_sample=5000)
    # output_train, output_test = convert_sample()
    test_lora()