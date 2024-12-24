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
    根据指定字段（如 name、level、address、phone、category）查找医疗机构
    """
    if field in ['category', 'level', 'address', 'phone', 'name']:
        # 对于这些字段，直接使用 Redis 集合进行查询
        org_ids = redis_client.smembers(f'{field}:{value}')

    # 返回查找到的医疗机构详细信息
    return [
            {'id': org_id, **redis_client.hgetall(org_id)}  # 将 org_id 加入返回数据
            for org_id in org_ids
        ]

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

    # 获取所有医疗机构的键
    all_org_keys = redis_client.keys("*")
    print(all_org_keys)

    # 遍历 Redis 中的所有医疗机构数据
    for org_id in all_org_keys:
        # 获取医疗机构的详细信息
        info = redis_client.hgetall(org_id)
        name = info.get('name', '')

        # 检查问题是否包含医疗机构名称
        if name and name in question:
            if "类别" in question and info.get("category"):
                can_or_not_answer.append({
                    "question": question,
                    "answer": info["category"]
                })
            elif "级别" in question and info.get("level"):
                can_or_not_answer.append({
                    "question": question,
                    "answer": info["level"]
                })
            elif "地址" in question and info.get("address"):
                can_or_not_answer.append({
                    "question": question,
                    "answer": info["address"]
                })
            elif "电话号码" in question and info.get("phone"):
                can_or_not_answer.append({
                    "question": question,
                    "answer": info["phone"]
                })
            elif "名称" in question:
                can_or_not_answer.append({
                    "question": question,
                    "answer": name
                })
            else:
                can_or_not_answer.append({
                    "question": question,
                    "answer": None
                })
            break
    else:
        # 如果没有找到匹配的医疗机构
        can_or_not_answer.append({
            "question": question,
            "answer": None
        })

    return can_or_not_answer