# -*- encoding: utf-8 -*-
'''
@File    :   rag.py
@Time    :   2024/07/05 20:36:07
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

chat with Qwen2 
'''

import datetime
import time
import json

import torch
from llama_index.core import Settings, PromptTemplate, Document
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


def completion_to_prompt(completion):
   return f"<|im_start|>system\n<|im_end|>\n<|im_start|>user\n{completion}<|im_end|>\n<|im_start|>assistant\n"


Settings.embed_model = HuggingFaceEmbedding(
    model_name = "/home/chenxiyuan/PetProjects/LLM/bge-m3"
)
Settings.transformations = [SentenceSplitter(chunk_size=1024)]

t_start = time.time()
# load saved index
try:
    print('Loading Stored Context')
    storage_context = StorageContext.from_defaults(persist_dir='data')
    index = load_index_from_storage(storage_context)
    print('Stored Context Loaded')
# generate index and store it locally
except Exception:
    print('Stored Context not Found, Generating One')
    page_json: str = 'data/page.json'
    with open(page_json) as f:
        all_page = json.load(f)
    
    list_document = []
    for i in all_page:
        # 筛选含有'scp'tag的页面
        if 'scp' in i['tag']:
            list_document.append(Document(text='\n'.join(i['text'])))
    
    index = VectorStoreIndex.from_documents(
        list_document,
        embed_model=Settings.embed_model,
        transformations=Settings.transformations)
    
    index.storage_context.persist('data')
    print('Stored Context Saved')
print('Time Cost:', str(datetime.timedelta.seconds(time.time()-t_start)))

def messages_to_prompt(messages):
    prompt = ""
    for message in messages:
        if message.role == "system":
            prompt += f"<|im_start|>system\n{message.content}<|im_end|>\n"
        elif message.role == "user":
            prompt += f"<|im_start|>user\n{message.content}<|im_end|>\n"
        elif message.role == "assistant":
            prompt += f"<|im_start|>assistant\n{message.content}<|im_end|>\n"

    if not prompt.startswith("<|im_start|>system"):
        prompt = "<|im_start|>system\n" + prompt

    prompt = prompt + "<|im_start|>assistant\n"

    return prompt


qwen2 = "/home/chenxiyuan/PetProjects/LLM/Qwen2-1.5B-Instruct"
Settings.llm = HuggingFaceLLM(
    model_name=qwen2,
    tokenizer_name=qwen2,
    context_window=5000,
    max_new_tokens=500,
    generate_kwargs={"temperature": 0.7, "top_k": 50, "top_p": 0.95},
    messages_to_prompt=messages_to_prompt,
    completion_to_prompt=completion_to_prompt,
    device_map="auto",
)

query_engine = index.as_query_engine()

def query(question: str = 'scp-6009和SCP-3966有关系吗？') -> str:
    response = query_engine.query(question).response
    return response