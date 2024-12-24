import os
import json
import redis
from redisgraph import Node, Graph
from django.conf import settings
from django.core.management.base import BaseCommand

from knowledge.management.commands.load_relation_from_medicaldata import extract_entities


class Command(BaseCommand):
    help = "Load medical data into Redis and RedisGraph"
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

        # 数据文件路径
        data_file_path = os.path.join(settings.BASE_DIR, 'static/json/ZJMedicalOrg.json')
        extract_entities()

        # 检查文件是否存在
        if not os.path.exists(data_file_path):
            self.stdout.write(self.style.ERROR(f"Data file not found: {data_file_path}"))
            return

        # 加载 JSON 数据
        with open(data_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 遍历每个医疗机构，并存储数据到 Redis 和 RedisGraph
        for org in data:
            org_id = org.get('@id')
            name = org.get('http://www.w3.org/2000/01/rdf-schema#label', [{}])[0].get('@value', '未知')
            category = org.get('http://cngraph.openkg.cn/#类别', [{}])[0].get('@value', '')
            level = org.get('http://cngraph.openkg.cn/#级别', [{}])[0].get('@value', '')
            address = org.get('http://cnschema.openkg.cn/#地址', [{}])[0].get('@value', '')
            phone = org.get('http://cnschema.openkg.cn/#电话号码', [{}])[0].get('@value', '')

            # 存储到 Redis 哈希表
            redis_client.hset(org_id, mapping={
                'name': name,
                'category': category,
                'level': level,
                'address': address,
                'phone': phone
            })

            # 存储到 Redis 集合
            redis_client.sadd(f'name:{name}', org_id)
            redis_client.sadd(f'category:{category}', org_id)
            redis_client.sadd(f'level:{level}', org_id)
            redis_client.sadd(f'address:{address}', org_id)
            redis_client.sadd(f'phone:{phone}', org_id)

            # 添加到 RedisGraph
            org_node = Node(label="MedicalOrg", properties={
                'id': org_id,
                'name': name,
                'category': category,
                'level': level,
                'address': address,
                'phone': phone
            })
            graph.add_node(org_node)

        # 提交图数据
        graph.commit()
        self.stdout.write(self.style.SUCCESS("Medical data successfully loaded into Redis and RedisGraph"))
        print("Medication data successfully loaded into Redis and RedisGraph")
