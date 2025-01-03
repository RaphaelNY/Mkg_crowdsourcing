import os
import json
import redis
from redisgraph import Node, Edge, Graph
from django.conf import settings
from django.core.management.base import BaseCommand


def extract_entities():
    with open('static/json/ZJMedicalOrg.json', 'r', encoding='utf-8') as file:
        medical_org_data = json.load(file)

    entities = []
    relationships = []

    def extract_entities_and_relationships(data):
        for org in data:
            if "http://www.w3.org/2000/01/rdf-schema#label" in org:
                org_label = org["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"]
            else:
                org_label = "未知"

            entity = {
                "label": org_label,
                "type": "医疗机构"
            }
            entities.append(entity)

            if "http://cngraph.openkg.cn/#类别" in org:
                category = org["http://cngraph.openkg.cn/#类别"][0]["@value"]
                relationships.append({
                    "source": org_label,
                    "relationship": "类别",
                    "target": category
                })
            if "http://cngraph.openkg.cn/#级别" in org:
                level = org["http://cngraph.openkg.cn/#级别"][0]["@value"]
                relationships.append({
                    "source": org_label,
                    "relationship": "级别",
                    "target": level
                })
            if "http://cnschema.openkg.cn/#地址" in org:
                address = org["http://cnschema.openkg.cn/#地址"][0]["@value"]
                relationships.append({
                    "source": org_label,
                    "relationship": "地址",
                    "target": address
                })
            if "http://cnschema.openkg.cn/#电话号码" in org:
                phone_number = org["http://cnschema.openkg.cn/#电话号码"][0]["@value"]
                relationships.append({
                    "source": org_label,
                    "relationship": "电话号码",
                    "target": phone_number
                })

    extract_entities_and_relationships(medical_org_data)

    result = {
        "entities": entities,
        "relationships": relationships
    }

    with open('static/json/extracted_entities_relationships.json', 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=4)

    print("实体及关系已保存到 extracted_entities_relationships.json 文件中")