import json
import redis

# 连接到Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# 读取JSON文件
with open('static/css/json/filtered_questions_with_answers.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 将数据存储到Redis中
for item in data:
    task_id = item["tasks_id"]
    r.set(task_id, json.dumps(item))

print("数据已成功导入到Redis数据库。")
