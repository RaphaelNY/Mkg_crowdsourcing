import jieba
import redis
from redisgraph import Graph, Node, Edge
from django.conf import settings

# Redis 连接
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# RedisGraph 连接
graph = Graph(settings.REDIS_GRAPH_NAME, redis_client)

def get_medical_org_by_id(org_id):
    """
    从 Redis 获取医疗机构的详细信息
    """
    return redis_client.hgetall(org_id)

def get_medical_orgs_by_category(category):
    """
    获取指定类别的医疗机构
    """
    org_ids = redis_client.smembers(f'category:{category}')
    return [redis_client.hgetall(org_id) for org_id in org_ids]

def get_medical_orgs_by_field(field, value):
    """
    根据指定字段（如 name、level、address、phone、category）模糊查找医疗机构
    """
    if field in ['category', 'level', 'address', 'phone', 'name']:
        org_ids = set()

        pattern = f'{field}:*{value}*'  # 模糊查询模式
        for key in redis_client.scan_iter(match=pattern):
            org_ids.update(redis_client.smembers(key))

        # 返回查找到的医疗机构详细信息
        return [
            {'id': org_id, **redis_client.hgetall(org_id)}  # 将 org_id 加入返回数据
            for org_id in org_ids
        ]
    else:
        raise ValueError(f"Invalid field: {field}. Valid fields are: ['category', 'level', 'address', 'phone', 'name']")


def get_graph_data_for_org(org_id):
    """
    获取指定医疗机构的图数据
    """
    graph = Graph(settings.REDIS_GRAPH_NAME, redis_client)
    query = f"MATCH (n:MedicalOrg {{id: '{org_id}'}}) RETURN n"
    results = graph.query(query)
    
    if not results.result_set:
        return None
    # 提取节点信息并构造返回的数据结构
    graph_data = []
    for record in results.result_set:
        node_data = record[0].properties
        graph_data.append(node_data)

    return graph_data

def get_graph_data():
    """
    获取 RedisGraph 中的所有图数据
    """
    query = "MATCH (n) RETURN n"
    result = graph.query(query)
    return [record[0].properties for record in result.result_set]

def check_question_and_generate_answer(question):
    can_or_not_answer = []

    # 提取问题中可能的医疗机构关键词（简单分词，或用正则等更复杂逻辑）
    question_keywords = set(jieba.lcut(question))
    print(f"Question keywords: {question_keywords}")

    # 使用 Redis 的通配符查找可能的机构
    matching_org_ids = []
    for keyword in question_keywords:
        # 检查是否存在名称相关的集合
        # 模糊检索所有包含 keyword 的集合键
        matching_keys = redis_client.scan_iter(match=f'name:*{keyword}*')

        potential_org_ids = set()
        for key in matching_keys:
            # 获取匹配到的集合中的所有值
            potential_org_ids.update(redis_client.smembers(key))
        if potential_org_ids:
            matching_org_ids.extend(potential_org_ids)

    # 去重
    matching_org_ids = list(set(matching_org_ids))

    if not matching_org_ids:
        # 如果没有匹配到任何机构
        return [{
            "question": question,
            "answer": None
        }]

    # 遍历匹配的机构并检查问题的具体属性
    for org_id in matching_org_ids:
        # 获取医疗机构的详细信息
        info = redis_client.hgetall(org_id)

        # 检查问题中是否包含需要查询的属性
        if "类别" in question and "category" in info:
            can_or_not_answer.append({
                "question": question,
                "answer": info["category"]
            })
        elif "级别" in question and "level" in info:
            can_or_not_answer.append({
                "question": question,
                "answer": info["level"]
            })
        elif "地址" in question and "address" in info:
            can_or_not_answer.append({
                "question": question,
                "answer": info["address"]
            })
        elif "电话号码" in question and "phone" in info:
            can_or_not_answer.append({
                "question": question,
                "answer": info["phone"]
            })
        elif "名称" in question:
            can_or_not_answer.append({
                "question": question,
                "answer": info["name"]
            })

    # 如果找不到匹配的问题答案，返回默认结果
    if not can_or_not_answer:
        can_or_not_answer.append({
            "question": question,
            "answer": None
        })

    print(f"Can or not answer: {can_or_not_answer}")
    return can_or_not_answer
