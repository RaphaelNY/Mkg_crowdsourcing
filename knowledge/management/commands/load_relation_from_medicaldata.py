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

class Command(BaseCommand):
    help = "Load medical data, including extracted entities and relationships, into Redis and RedisGraph"
    print("Executing load_medical_data command...")

    def handle(self, *args, **kwargs):
        # 连接 Redis 和 RedisGraph
        redis_client = redis.StrictRedis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        graph = Graph(settings.REDIS_GRAPH_NAME, redis_client)
        
        extract_entities()

        # 提取实体和关系文件路径
        extracted_data_file_path = os.path.join(settings.BASE_DIR, 'static/json/extracted_entities_relationships.json')

        # 检查文件是否存在
        if not os.path.exists(extracted_data_file_path):
            self.stdout.write(self.style.ERROR(f"Extracted data file not found: {extracted_data_file_path}"))
            return

        # 加载提取的实体和关系数据
        with open(extracted_data_file_path, 'r', encoding='utf-8') as file:
            extracted_data = json.load(file)

        entities = extracted_data.get("entities", [])
        relationships = extracted_data.get("relationships", [])

        # 遍历实体并存储到 Redis 和 RedisGraph
        for entity in entities:
            label = entity.get('label', '未知')
            entity_type = entity.get('type', '未知')

            # 存储到 Redis 哈希表
            redis_client.hset(f"entity:{label}", mapping={
                'label': label,
                'type': entity_type
            })

            # 添加到 RedisGraph
            entity_node = Node(label=entity_type, properties={
                'label': label,
                'type': entity_type
            })
            graph.add_node(entity_node)

        # 遍历关系并存储到 RedisGraph
        for relationship in relationships:
            source = relationship.get("source", "未知")
            relationship_type = relationship.get("relationship", "未知")
            target = relationship.get("target", "未知")

            # 存储到 Redis 集合（索引方式）
            redis_client.sadd(f"relationship:{relationship_type}", f"{source}->{target}")

            # 在 RedisGraph 中添加边
            source_node = Node(label="Entity", properties={'label': source})
            target_node = Node(label="Entity", properties={'label': target})
            edge = Edge(source_node, relationship_type, target_node)

            # 避免重复添加同名节点
            graph.add_node(source_node)
            graph.add_node(target_node)
            graph.add_edge(edge)

        # 提交图数据
        graph.commit()
        self.stdout.write(self.style.SUCCESS("Extracted entities and relationships successfully loaded into Redis and RedisGraph"))
        print("Extracted entities and relationships successfully loaded into Redis and RedisGraph")
