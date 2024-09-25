# -*- encoding: utf-8 -*-
'''
@File    :   graph_utilities.py
@Time    :   2024/07/24 12:02:00
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com

IMPORTANT: 不能在查询字符串中直接使用 $head、$relationship 和 $tail 作为变量名称
传入的参数只能作为 value of property 使用
'''

import json
from typing import Generator

from langchain_community.graphs import Neo4jGraph


def create_index(
    graph: Neo4jGraph,
    label: str,
    property: str,
) -> None:
    query = f'CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property})'
    graph.query(query)


def create_node(
    graph: Neo4jGraph,
    label: str,
    list_property_dict: list[dict],
    merge: bool = False,
    property_not_null: str = None,
) -> None:
    str_property = []
    for key in list_property_dict[0].keys():
        str_property.append(f'{key}: data.{key}')
    str_property = ', '.join(str_property)
    verb = 'MERGE' if merge else 'CREATE'
    query = """UNWIND $list_property_dict AS data
    %s (n:%s {%s})"""%(verb, label, str_property)
    # for graph.query(**kwargs) to work, modify the functions as:
    # def query(self, query: str, params: dict = {}, **kwargs) -> List[Dict[str, Any]]:
    # ...
    #             data = session.run(Query(text=query, timeout=self.timeout), params, **kwargs)
    # ...
    graph.query(query, list_property_dict=list_property_dict)


def print_schema(graph: Neo4jGraph) -> str:
    graph.refresh_schema()
    s = graph.get_schema
    print(s)
    return s


def delete_all(graph: Neo4jGraph) -> None:
    graph.query('''MATCH (n)
    OPTIONAL MATCH (n)-[r]-()
    DETACH DELETE n, r''')
    # drop all indexes and constraints, from ChatGPT 3.5!
    graph.query('''CALL apoc.schema.assert({},{}) YIELD label, key, action
    RETURN label, key, action;''')


def get_node_property(
    graph: Neo4jGraph,
    label: str = 'Tag',
    property: str = 'tag',
) -> list[str]:
    list_dict = graph.query(f'MATCH (n:{label}) RETURN COLLECT(n.{property}) AS result')
    return list_dict[0]['result']


def count_node(
    graph: Neo4jGraph,
    label: str = None,
) -> None:
    label = '' if label is None else f':{label}'
    query = f'''MATCH (node{label})
    RETURN count(node)'''
    print(f'(node{label}):', graph.query(query))


def create_rel_multitail(
    graph: Neo4jGraph,
    head_label: str = 'ScpOject',
    head_property: str = 'item_number',
    head_value = '',
    tail_label: str = 'Tag',
    tail_property: str = 'tag',
    list_tail_value: list = [],
    relationship: str = 'HAS_TAG',
    merge: bool = False,
) -> None:
    if len(list_tail_value) == 0:
        return None
    list_tail_value = [{'value': i} for i in list_tail_value]
    head_value = repr(head_value)
    q_head = 'MATCH (head:%s {%s: %s})'%(head_label, head_property, head_value)
    q_unwind = 'UNWIND $list_tail_value AS tail_param'
    q_tail = 'MATCH (tail:%s {%s: tail_param.value})'%(tail_label, tail_property)
    verb = 'MERGE' if merge else 'CREATE'
    q_create = '%s (head)-[:%s]->(tail)'%(verb, relationship)
    query = '\n'.join([q_head, q_unwind, q_tail, q_create])
    graph.query(query, list_tail_value=list_tail_value)


def create_rel_multihead(
    graph: Neo4jGraph,
    head_label: str = 'ScpOject',
    head_property: str = 'item_number',
    list_head_value = [],
    tail_label: str = 'Tag',
    tail_property: str = 'tag',
    tail_value: list = '',
    relationship: str = 'HAS_TAG',
    merge: bool = False,
) -> None:
    if len(list_head_value) == 0:
        return None
    list_head_value = [{'value': i} for i in list_head_value]
    tail_value = repr(tail_value)
    q_unwind = 'UNWIND $list_head_value AS head_param'
    q_head = 'MATCH (head:%s {%s: head_param.value})'%(head_label, head_property)
    q_tail = 'MATCH (tail:%s {%s: %s})'%(tail_label, tail_property, tail_value)
    verb = 'MERGE' if merge else 'CREATE'
    q_create = '%s (head)-[:%s]->(tail)'%(verb, relationship)
    query = '\n'.join([q_unwind, q_head, q_tail, q_create])
    graph.query(query, list_head_value=list_head_value)


def count_rel(
    graph: Neo4jGraph,
    head: str = None,
    relationship: str = None,
    tail: str = None,
) -> None:
    query = f"""MATCH relationship=(head:{head})-[r:{relationship}]->(tail:{tail})
    RETURN count(relationship)"""
    print(f'relationship=({head})-[{relationship}]->({tail}):', 
          graph.query(query))