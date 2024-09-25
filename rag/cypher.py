# -*- encoding: utf-8 -*-
'''
@File    :   graph_chat.py
@Time    :   2024/07/25 16:49:45
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
https://qwen.readthedocs.io/zh-cn/latest/framework/Langchain.html#
https://neo4j.com/labs/genai-ecosystem/langchain/#_neo4j_graph
https://python.langchain.com/v0.2/docs/integrations/llms/tongyi/#using-in-a-chain
https://python.langchain.com/v0.2/docs/integrations/providers/neo4j/#graphcypherqachain
https://python.langchain.com/v0.2/docs/integrations/graphs/neo4j_cypher/
https://api.python.langchain.com/en/latest/chains/langchain_community.chains.graph_qa.cypher.GraphCypherQAChain.html
https://python.langchain.com/v0.2/docs/tutorials/graph/
https://python.langchain.com/v0.2/docs/how_to/graph_prompting/#few-shot-examples
'''

import torch
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from transformers import AutoModelForCausalLM, AutoTokenizer
from abc import ABC
from langchain.llms.base import LLM
from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_community.chains.graph_qa.cypher import CYPHER_GENERATION_PROMPT
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI

from openai_api import OPENAI_API_BASE, OPENAI_API_KEY


device = "cuda" # the device to load the model onto
# dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-1.5B-Instruct"
# dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-7B-Instruct"
dir_model = "/home/chenxiyuan/PetProjects/LLM/Qwen2-7B-Instruct-AWQ"
model = AutoModelForCausalLM.from_pretrained(
    dir_model,
    torch_dtype=torch.float16,
    # torch_dtype="auto",
    device_map="auto",
    local_files_only=True,
    )
tokenizer = AutoTokenizer.from_pretrained(
    dir_model,
    local_files_only=True,
    )

class Qwen(LLM, ABC):
    max_token: int = 10000
    temperature: float = 0
    top_p = 0.9
    history_len: int = 3

    def __init__(self):
        super().__init__()

    @property
    def _llm_type(self) -> str:
        return "Qwen"

    @property
    def _history_len(self) -> int:
        return self.history_len

    def set_history_len(self, history_len: int = 10) -> None:
        self.history_len = history_len

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
    ) -> str:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(device)
        generated_ids = model.generate(
            model_inputs.input_ids,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"max_token": self.max_token,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "history_len": self.history_len,
                }



chatgpt = ChatOpenAI(
    openai_api_base=OPENAI_API_BASE,
    openai_api_key=OPENAI_API_KEY,
    temperature=0
)


# these cypher prompts have to be customized for specific schema
# ChatGPT generate cypher very well
cypher_prompt_example = [
    {
        "question": "scp-1446的特殊收容措施",
        "query": "MATCH (object:ScpObject {{item_number: 'scp-1446'}}) RETURN object.special_containment_procedure",
    },
    {
        "question": "哪些项目有威尔逊野生动物的标签？",
        "query": "MATCH (object:ScpObject)-[:HAS_TAG]->(:Tag {{tag:'威尔逊野生动物'}}) RETURN object.item_number",
    },
    {
        "question": "一共有多少个scp项目有“搞笑”或“人形生物”的标签？",
        "query": "MATCH (object:ScpObject)-[:HAS_TAG]->(tag:Tag) WHERE tag.tag = '搞笑' OR tag.tag = '人形生物' RETURN COUNT(object) AS count;",
    },
    {
        "question": "MTF Beta-2 协助收容了几个基金会项目？",
        "query": "MATCH (tf:TaskForce) WHERE tf.name CONTAINS 'Beta-2' UNWIND tf.object_contained AS object RETURN COUNT(object) AS count",
    },
    {
        "question": "所有和Harold Blank博士有关的scp项目",
        "query": "MATCH (object:ScpObject)-[:HAS_TAG]->(tag:Tag)-[:IS_TAG_OF]->(character:Character {{name: 'Harold Blank博士'}}) RETURN COLLECT(object.item_number)",
    },
    {
        "question": "标签为dan博士的人物角色",
        "query": "MATCH (:Tag {{tag: 'dan博士'}})-[:IS_TAG_OF]->(character:Character) RETURN character",
    },
    # {
    #     "question": "How many artists are there?",
    #     "query": "MATCH (a:Person)-[:ACTED_IN]->(:Movie) RETURN count(DISTINCT a)",
    # },
    # {
    #     "question": "Which actors played in the movie Casino?",
    #     "query": "MATCH (m:Movie {{title: 'Casino'}})<-[:ACTED_IN]-(a) RETURN a.name",
    # },
    # {
    #     "question": "How many movies has Tom Hanks acted in?",
    #     "query": "MATCH (a:Person {{name: 'Tom Hanks'}})-[:ACTED_IN]->(m:Movie) RETURN count(m)",
    # },
    # {
    #     "question": "List all the genres of the movie Schindler's List",
    #     "query": "MATCH (m:Movie {{title: 'Schindler\\'s List'}})-[:IN_GENRE]->(g:Genre) RETURN g.name",
    # },
    # {
    #     "question": "Which actors have worked in movies from both the comedy and action genres?",
    #     "query": "MATCH (a:Person)-[:ACTED_IN]->(:Movie)-[:IN_GENRE]->(g1:Genre), (a)-[:ACTED_IN]->(:Movie)-[:IN_GENRE]->(g2:Genre) WHERE g1.name = 'Comedy' AND g2.name = 'Action' RETURN DISTINCT a.name",
    # },
    # {
    #     "question": "Which directors have made movies with at least three different actors named 'John'?",
    #     "query": "MATCH (d:Person)-[:DIRECTED]->(m:Movie)<-[:ACTED_IN]-(a:Person) WHERE a.name STARTS WITH 'John' WITH d, COUNT(DISTINCT a) AS JohnsCount WHERE JohnsCount >= 3 RETURN d.name",
    # },
    # {
    #     "question": "Identify movies where directors also played a role in the film.",
    #     "query": "MATCH (p:Person)-[:DIRECTED]->(m:Movie), (p)-[:ACTED_IN]->(m) RETURN m.title, p.name",
    # },
    # {
    #     "question": "Find the actor with the highest number of movies in the database.",
    #     "query": "MATCH (a:Actor)-[:ACTED_IN]->(m:Movie) RETURN a.name, COUNT(m) AS movieCount ORDER BY movieCount DESC LIMIT 1",
    # },
]
example_prompt = PromptTemplate.from_template(
    "User input: {question}\nCypher query: {query}"
)
cypher_prompt = FewShotPromptTemplate(
    examples=cypher_prompt_example,
    example_prompt=example_prompt,
    # prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries.",
    prefix="You are a Neo4j expert"+CYPHER_GENERATION_PROMPT.template,
    suffix="User input: {question}\nCypher query: ",
    input_variables=["question", "schema"],
)


if __name__ == '__main__':
    # start neo4j server: sudo neo4j start
    graph = Neo4jGraph(
        url="bolt://localhost:7687", 
        username="neo4j", 
        password="password",
    )
    # print_schema(graph)
    qwen = Qwen()
    # qwen_cypher = QwenCypher()

    chain = GraphCypherQAChain.from_llm(
        qwen, graph=graph, verbose=True, 
        cypher_prompt=cypher_prompt, 
        cypher_llm=chatgpt,
        
    )
    # qwen2-7B：生成的cpyher语法出错：
    # "MATCH (scp:Object WHERE scp.item_number = 'scp-cn-2452' RETURN scp.description"
    # 加入cypher_prompt也没有改善
    # qwen2-1.5B：加入cypher_prompt后生成cypher语法比7B好，但稳定性较差
    # 需要多次尝试才能输出正确答案
    # question = '一共有多少个scp项目有“搞笑”或“人形生物”的标签？'
    # question = '给出3个等级为keter的scp项目的描述'
    # question = '所有和dan博士有关的scp项目'
    question = '列出所有与黑皇后有关的SCP项目编号'
    prompt = '\n直接输出提供的信息，不要进行任何修改和删减'
    answer = chain.run(question)
    print(answer)