# -*- encoding: utf-8 -*-
'''
@File    :   build_graph.py
@Time    :   2024/07/10 00:24:49
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''



import json

from langchain_community.graphs import Neo4jGraph

from graph_utilities import print_schema, delete_all
from graph_utilities import create_node, count_node, create_index
from graph_utilities import create_rel_multitail, count_rel


# start neo4j server: sudo neo4j start
graph = Neo4jGraph(
    url="bolt://localhost:7687", 
    username="neo4j", 
    password="password",
    )


def create_node_simple(
    label: str,
    json_path: str = None,
    index: str = None,
) -> None:
    if json_path is None:
        json_path = f'../data/{label.lower()}.json'    
    with open(json_path) as f:
        list_dict: list[dict] = json.load(f)
    create_node(graph, label, list_dict)
    create_index(graph, label, index)
    count_node(graph, label)


def create_tag(json_path: str = None) -> None:
    create_node_simple('Tag', json_path, 'tag')


def create_facility(json_path: str = None) -> None:
    create_node_simple('Facility', json_path, 'name')


def create_taskforce(json_path: str = None) -> None:
    create_node_simple('TaskForce', json_path, 'name')  


def create_node_as_tail(
    label: str,
    json_path: str = None,
    index: str = None,
    head_label: str = 'Tag',
    property: str = 'tag',
    relationship: str = 'IS_TAG_OF',
) -> None:
    if json_path is None:
        json_path = f'../data/{label.lower()}.json'
    with open(json_path) as f:
        list_dict: list[dict] = json.load(f)
    create_node(graph, label, list_dict)
    create_index(graph, label, index)
    count_node(graph, label)
    for i in list_dict:
        value = i[property]
        if value is not None:
            create_rel_multitail(
                graph, 
                head_label, property, value, 
                label, property, [value], 
                relationship)
    count_rel(graph, head_label, relationship, label) 


def create_goi(json_path: str = None) -> None:
    create_node_as_tail('GroupOfInterest', json_path, 'name')
    

def create_character(json_path: str = None) -> None:
    create_node_as_tail('Character', json_path, 'name')
    

def create_canon(json_path: str = None) -> None:
    create_node_as_tail('Canon', json_path, 'name', property='address')   


def create_series(json_path: str = None) -> None:
    create_node_as_tail('Series', json_path, 'name')


def create_scp(json_path: str = '../data/scp.json') -> None:
    with open(json_path) as f:
        list_dict: list[dict] = json.load(f)
    label = 'ScpObject'
    index = 'item_number'
    create_node(graph, label, list_dict)
    create_index(graph, label, index)
    count_node(graph, label)
    tail_label = 'Tag'
    tail_property = 'tag'
    relationship = 'HAS_TAG'
    for i in list_dict:
        tail_value = i[tail_property]
        if len(tail_value) > 0:
            # TODO: 大量磁盘活动(50%)（95.62 sec）
            create_rel_multitail(
                graph, 
                label, index, i[index], 
                tail_label, tail_property, tail_value, 
                relationship)
    count_rel(graph, label, relationship, tail_label) 


if __name__ == '__main__':
    pass
    import time
    delete_all(graph)
    t_start = time.time()
    create_tag()
    create_facility()
    create_taskforce()
    create_goi()
    create_canon()
    create_character()
    create_series()
    create_scp()
    print('Time Cost: %.2f sec'%(time.time()-t_start))
    # 95.62 sec 2024年7月25日02点43分