# -*- encoding: utf-8 -*-
'''
@File    :   oneke.py
@Time    :   2024/07/06 13:01:02
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

build knowledge graph from SCP pages with OneKE
'''

import json

import torch
from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig,
    BitsAndBytesConfig
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = '/home/chenxiyuan/PetProjects/LLM/OneKE'
config = AutoConfig.from_pretrained(model_path, trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)


# 4bit量化OneKE
quantization_config=BitsAndBytesConfig(     
    load_in_4bit=True,
    llm_int8_threshold=6.0,
    llm_int8_has_fp16_weight=False,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)
print('Model Quantized')

model = AutoModelForCausalLM.from_pretrained(
    model_path,
    config=config,
    device_map="auto",  
    quantization_config=quantization_config,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.eval()
print('Model Loaded')

with open('oneke_example.json') as f:
    oneke_example = json.load(f)
instruction_mapper = oneke_example['instruction_mapper']
# 指令列表
# 各个任务的推荐切分长度
split_num_mapper = {
    'NER':6, 'RE':4, 'EE':4, 'EET':4, 'EEA':4, 'KG':1
}


def get_instruction(
    language: str = 'zh', 
    task: str = 'NER', 
    schema: list[str] | dict | list[dict] = ['人名', '时间', '地点'], 
    example: list[dict] = None,
    input: str = '2010年10月5日\nSite-84\n日本福冈\n蒋渭火博士您好：\n我是冈见亮辅，Site-84神经科学部的3级研究员。他们安排我和你在这个项目上合作。我已经看了你发来的SCP-6009材料，还有你对6009-Catena的形成做出的假设。',
    ) -> list[str]:
    if example is None:
        dict_instruct = {
            'instruction':instruction_mapper[task+language], 
            'schema':schema, 
            'input':input
            }
    else:
        dict_instruct = {
            'instruction':instruction_mapper[task+language], 
            'schema':schema, 
            'example':example,
            'input':input
            }
    sintruct = json.dumps(dict_instruct, ensure_ascii=False)
    return sintruct


def get_response(sintruct: str) -> str:
    system_prompt = '<<SYS>>\nYou are a helpful assistant. 你是一个乐于助人的助手。\n<</SYS>>\n\n'
    sintruct = '[INST] ' + system_prompt + sintruct + '[/INST]'
    input_ids = tokenizer.encode(sintruct, return_tensors="pt").to(device)
    input_length = input_ids.size(1)
    generation_output = model.generate(input_ids=input_ids, generation_config=GenerationConfig(max_length=1024, max_new_tokens=512, return_dict_in_generate=True), pad_token_id=tokenizer.eos_token_id)
    generation_output = generation_output.sequences[0]
    generation_output = generation_output[input_length:]
    output = tokenizer.decode(generation_output, skip_special_tokens=True)

    return output


if __name__ == '__main__':
    sintruct = get_instruction()
    response = get_response(sintruct)
    print(response)