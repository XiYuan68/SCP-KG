# -*- encoding: utf-8 -*-
'''
@File    :   build_graph.py
@Time    :   2024/07/10 00:24:49
@Author  :   Chen XiYuan 
@Version :   1.0
@Contact :   cxy13.ok@163.com
'''

from copy import deepcopy
import json

from langchain_community.graphs import Neo4jGraph

from graph_utilities import print_schema, delete_all, get_node_property
from graph_utilities import create_node, count_node, create_index
from graph_utilities import create_rel_multitail, create_rel_multihead, count_rel


# start neo4j server: sudo neo4j start
# if showing error: The credentials you provided were valid, but must be changed before you can use this instance.
# change the default password to "password" by running following command in terminal:
# sudo neo4j-admin dbms set-initial-password password
graph = Neo4jGraph(
    url="bolt://localhost:7687", 
    username="neo4j", 
    password="password",
    )


def create_node_simple(
    label: str,
    json_path: str = None,
    index: str = None,
    func = None,
) -> None:
    if json_path is None:
        json_path = f'../data/{label.lower()}.json'    
    with open(json_path) as f:
        list_dict: list[dict] = json.load(f)
    if func is not None:
        list_dict_new = [func(i) for i in list_dict]
        list_dict = list_dict_new
    create_node(graph, label, list_dict)
    create_index(graph, label, index)
    count_node(graph, label)


def create_tag(json_path: str = None) -> None:
    create_node_simple('Tag', json_path, 'tag')


def create_facility(json_path: str = None) -> None:
    create_node_simple('Facility', json_path, 'name')


def create_taskforce(json_path: str = None) -> None:
    create_node_simple('TaskForce', json_path, 'name')  


def create_tag_simple(list_tag: list[str]) -> None:
    dict_empty = { "tag": "", "tag_english": "", "description": "", 
                  "address": "", "type": []}
    list_dict = []
    set_tag_exist = set(get_node_property(graph))
    for i in set(list_tag):
        if i not in set_tag_exist:
            dict_tag = deepcopy(dict_empty)
            dict_tag['tag'] = i
            list_dict.append(dict_tag)

    # early stop if all tag-nodes already exist
    if len(list_dict) == 0:
        return None

    create_node(graph, 'Tag', list_dict)
    create_index(graph, 'Tag', 'tag')
    count_node(graph, 'Tag')


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

    # TODO: create tag nodes that not existing
    if head_label == 'Tag' and property == 'tag' and relationship == 'IS_TAG_OF':
        create_tag_simple([i['tag'] for i in list_dict])
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


def create_attribute(json_path: str = None) -> None:
    create_node_as_tail('Attribute', json_path, 'name')


def create_canon(json_path: str = None) -> None:
    create_node_as_tail('Canon', json_path, 'name')   


def create_series(json_path: str = None) -> None:
    create_node_as_tail('Series', json_path, 'name')


def create_scp(
    json_path: str = '../data/scp.json',
    json_facility: str = '../data/facility.json',
    json_taskforce: str = '../data/taskforce.json',
) -> None:
    with open(json_path) as f:
        list_dict: list[dict] = json.load(f)
    label = 'ScpObject'
    index = 'item_number'

    # create tag nodes if not existing
    list_tag = []
    for i in list_dict:
        list_tag += i['tag']
    create_tag_simple(list_tag)
    
    create_node(graph, label, list_dict)
    create_index(graph, label, index)
    count_node(graph, label)

    node = 'Facility'
    relation = 'IS_CONTAINED_IN_FACILITY'
    scp_contained = set()
    with open(json_facility) as f:
        list_facility = json.load(f)
    for i in list_facility:
        scp_uncontained = set(i['object_contained']).difference(scp_contained)
        if len(scp_uncontained) == 0:
            continue
        scp_contained.update(i['object_contained'])
        create_rel_multihead(
            graph, 
            label, index, scp_uncontained, 
            node, 'facility_index', i['facility_index'], 
            relation            
        )
    count_rel(graph, label, relation, node)

    node = 'TaskForce'
    relation = 'IS_CONTAINED_BY_TASKFORCE'
    scp_contained = set()
    with open(json_taskforce) as f:
        list_taskforce = json.load(f)
    for i in list_taskforce:
        create_rel_multihead(
            graph, 
            label, index, i['object_contained'], 
            node, 'name', i['name'], 
            relation            
        )
    count_rel(graph, label, relation, node)

    def create_tail(
        scp_dict: dict,
        tail_label: str,
        relationship: str,
        tail_property: str = 'tag'
    ) -> None:
        tail_value = scp_dict[tail_property]
        if len(tail_value) > 0:
            create_rel_multitail(
                graph, 
                label, index, scp_dict[index], 
                tail_label, tail_property, tail_value, 
                relationship)

    # build relations of each SCP object
    node2relation = {
        'Tag': 'HAS_TAG',
        'Attribute': 'HAS_ATTRIBUTE',
        'Character': 'RELATE_TO_CHARACTER',
        'GroupOfInterest': 'RELATE_TO_GROUP',
        'Series': 'BELONG_T0_SERIES',
        'Canon': 'BELONG_T0_CANON',
    }
    for node, relation in node2relation.items():
        for i in list_dict:
            create_tail(i, node, relation)
        count_rel(graph, label, relation, node)
    

def find_node(
    graph: Neo4jGraph,
    label: str = 'Tag',
    property: str = 'tag',
    value: str = 'blank博士',
) -> list[dict]:
    query = "MATCH (n:%s {%s: '%s'}) RETURN n"%(label, property, value)
    return graph.query(query)


if __name__ == '__main__':
    pass
    import time
    delete_all(graph)
    t_start = time.time()
    create_tag()
    create_facility()
    create_taskforce()
    create_goi(json_path='../data/goi.json')
    create_canon()
    create_character()
    create_series()
    create_attribute()
    create_scp()
    print('Time Cost: %.2f sec'%(time.time()-t_start))
    # 362.09 sec 2024年8月28日00点54分