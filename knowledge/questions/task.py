#生成问题


import json
import random

# 读取JSON文件
with open('static\css\json\ZJMedicalOrg.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# 获取所有医疗机构的名称和地址
medical_org_info = [(entry["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"], 
                     entry["http://cngraph.openkg.cn/#类别"][0]["@value"] if "http://cngraph.openkg.cn/#类别" in entry else None,
                     entry["http://cngraph.openkg.cn/#级别"][0]["@value"] if "http://cngraph.openkg.cn/#级别" in entry else None,
                     entry["http://cnschema.openkg.cn/#地址"][0]["@value"] if "http://cnschema.openkg.cn/#地址" in entry else None)
                    for entry in data if "http://www.w3.org/2000/01/rdf-schema#label" in entry]

# 获取所有医疗机构的名称列表
medical_org_names = [entry[0] for entry in medical_org_info]

# 定义生成问题的函数
def generate_questions(entry):
    name, category, level, address = entry
    questions = []

    # 基本信息
    random_name = random.choice(medical_org_names)
    questions.append(f"{random_name}的类别是什么？")
    questions.append(f"{random_name}的级别是怎样的？")
    questions.append(f"{random_name}的地址在哪里？")
    questions.append(f"{random_name}的电话号码是多少？")

    # 按地址分类
    if address:
        address_parts = address.split('市')
        if len(address_parts) > 1:
            city = address_parts[0] + '市'
            district = address_parts[1].split('区')[0] + '区'
            questions.append(f"{city}{district}有哪些推荐的医疗机构？")
            questions.append(f"{city}{district}最好的医疗机构是什么？")
            questions.append(f"如何前往{city}{district}的{random.choice(medical_org_info)[0]}？")
            questions.append(f"{random.choice(medical_org_info)[0]}在{city}{district}的地址是什么？")

    # 病人满意度
    questions.append(f"{name}的病人满意度评分是多少？")
    questions.append(f"{name}的病人对这里的服务评价如何？")

    # 设备
    questions.append(f"{name}配备的先进的诊疗设备有哪些？")
    questions.append(f"{name}拥有的最新的医疗设备是什么？")

    # 药品供应
    questions.append(f"{name}是否有自营的药房？")
    questions.append(f"{name}提供的常用的药品有哪些？")

    # 急诊服务
    questions.append(f"{name}是否提供24小时急诊服务？")

    # 类别和级别
    if category:
        questions.append(f"{name}属于哪一类医疗机构？")
        questions.append(f"{name}的类别是什么？")

    if level:
        questions.append(f"{name}的级别是什么？")
        questions.append(f"{name}属于什么级别？")
        questions.append(f"{name}是{level}医疗机构吗？")
    
    return questions

# 遍历数据集并生成问题
all_questions = []
for entry in medical_org_info:
    questions = generate_questions(entry)
    all_questions.extend(questions)

# 对生成的问题随机选择一部分保存
num_questions_to_save = 200  # 您可以根据需要调整随机选择的问题数量
selected_questions = random.sample(all_questions, min(num_questions_to_save, len(all_questions)))

# 将随机选择的问题保存到JSON文件
with open('static\css\json\questions.json', 'w', encoding='utf-8') as outfile:
    json.dump(selected_questions, outfile, ensure_ascii=False, indent=4)

print("随机选择的问题已保存到questions.json文件中。")
