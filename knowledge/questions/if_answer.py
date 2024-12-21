#检查问题是否可以回答，生成can_answer.json和cannot_answer.json
######
####

import json
import random

# 读取questions.json文件
with open('static\css\json\questions.json', 'r', encoding='utf-8') as file:
    questions = json.load(file)

# 读取ZJMedicalOrg.json文件
with open('static\css\json\ZJMedicalOrg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 获取所有医疗机构的名称和相关信息
medical_org_info = {entry["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"]: {
                        "category": entry.get("http://cngraph.openkg.cn/#类别", [{}])[0].get("@value"),
                        "level": entry.get("http://cngraph.openkg.cn/#级别", [{}])[0].get("@value"),
                        "address": entry.get("http://cnschema.openkg.cn/#地址", [{}])[0].get("@value"),
                        "phone": entry.get("http://cnschema.openkg.cn/#电话号码", [{}])[0].get("@value")
                    } for entry in data if "http://www.w3.org/2000/01/rdf-schema#label" in entry}

# 定义检查问题并生成答案的函数
def check_question_and_generate_answer(question):
    can_answer = []
    cannot_answer = []

    # 提取问题中的医疗机构名称
    for name, info in medical_org_info.items():
        if name in question:
            if "类别" in question and info["category"]:
                can_answer.append({
                    "question": question,
                    "answer": info["category"]
                })
            elif "级别" in question and info["level"]:
                can_answer.append({
                    "question": question,
                    "answer": info["level"]
                })
            elif "地址" in question and info["address"]:
                can_answer.append({
                    "question": question,
                    "answer": info["address"]
                })
            elif "电话号码" in question and info["phone"]:
                can_answer.append({
                    "question": question,
                    "answer": info["phone"]
                })
            elif "名称" in question:
                can_answer.append({
                    "question": question,
                    "answer": name
                })
            else:
                cannot_answer.append({
                    "question": question,
                    "answer": None
                })
            break
    else:
        cannot_answer.append({
            "question": question,
            "answer": None
        })

    return can_answer, cannot_answer

# 遍历questions并进行检查
all_can_answer = []
all_cannot_answer = []

for question in questions:
    can_answer, cannot_answer = check_question_and_generate_answer(question)
    all_can_answer.extend(can_answer)
    all_cannot_answer.extend(cannot_answer)

# 将能回答和不能回答的问题分别保存到JSON文件中
with open('static\css\json\can_answer.json', 'w', encoding='utf-8') as can_file:
    json.dump(all_can_answer, can_file, ensure_ascii=False, indent=4)

with open('static\css\json\cannot_answer.json', 'w', encoding='utf-8') as cannot_file:
    json.dump(all_cannot_answer, cannot_file, ensure_ascii=False, indent=4)

print("检查完成，能回答和不能回答的问题已分别保存到can_answer.json和cannot_answer.json文件中。")
