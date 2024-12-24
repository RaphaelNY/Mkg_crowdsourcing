import json
import random
from datetime import datetime, timedelta
from pytz import timezone
from cemotion import Cegmentor

# 设定时区为 Asia/Shanghai
tz = timezone('Asia/Shanghai')

# 定义默认的截止时间函数
def default_leave_time1():
    return datetime.now(tz) + timedelta(days=7)

# 生成问题的脚本内容
def generate_questions():
    with open('static/json/ZJMedicalOrg.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    medical_org_info = [(entry["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"], 
                         entry["http://cngraph.openkg.cn/#类别"][0]["@value"] if "http://cngraph.openkg.cn/#类别" in entry else None,
                         entry["http://cngraph.openkg.cn/#级别"][0]["@value"] if "http://cngraph.openkg.cn/#级别" in entry else None,
                         entry["http://cnschema.openkg.cn/#地址"][0]["@value"] if "http://cnschema.openkg.cn/#地址" in entry else None)
                        for entry in data if "http://www.w3.org/2000/01/rdf-schema#label" in entry]

    medical_org_names = [entry[0] for entry in medical_org_info]

    def generate_questions(entry):
        name, category, level, address = entry
        questions = []

        random_name = random.choice(medical_org_names)
        questions.append(f"{random_name}的类别是什么？")
        questions.append(f"{random_name}的级别是怎样的？")
        questions.append(f"{random_name}的地址在哪里？")
        questions.append(f"{random_name}的电话号码是多少？")

        if address:
            address_parts = address.split('市')
            if len(address_parts) > 1:
                city = address_parts[0] + '市'
                district = address_parts[1].split('区')[0] + '区'
                questions.append(f"{city}{district}有哪些推荐的医疗机构？")
                questions.append(f"{city}{district}最好的医疗机构是什么？")
                questions.append(f"如何前往{city}{district}的{random.choice(medical_org_info)[0]}？")
                questions.append(f"{random.choice(medical_org_info)[0]}在{city}{district}的地址是什么？")

        questions.append(f"{name}的病人满意度评分是多少？")
        questions.append(f"{name}的病人对这里的服务评价如何？")
        questions.append(f"{name}配备的先进的诊疗设备有哪些？")
        questions.append(f"{name}拥有的最新的医疗设备是什么？")
        questions.append(f"{name}是否有自营的药房？")
        questions.append(f"{name}提供的常用的药品有哪些？")
        questions.append(f"{name}是否提供24小时急诊服务？")
        if category:
            questions.append(f"{name}属于哪一类医疗机构？")
            questions.append(f"{name}的类别是什么？")
        if level:
            questions.append(f"{name}的级别是什么？")
            questions.append(f"{name}属于什么级别？")
            questions.append(f"{name}是{level}医疗机构吗？")
    
        return questions

    all_questions = []
    for entry in medical_org_info:
        questions = generate_questions(entry)
        all_questions.extend(questions)

    num_questions_to_save = 200
    selected_questions = random.sample(all_questions, min(num_questions_to_save, len(all_questions)))

    with open('static/json/questions.json', 'w', encoding='utf-8') as outfile:
        json.dump(selected_questions, outfile, ensure_ascii=False, indent=4)

    print("随机选择的问题已保存到questions.json文件中。")

# 检查问题是否可以回答并生成can_answer.json和cannot_answer.json
def check_questions():
    with open('static/json/questions.json', 'r', encoding='utf-8') as file:
        questions = json.load(file)

    with open('static/json/ZJMedicalOrg.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    medical_org_info = {entry["http://www.w3.org/2000/01/rdf-schema#label"][0]["@value"]: {
                            "category": entry.get("http://cngraph.openkg.cn/#类别", [{}])[0].get("@value"),
                            "level": entry.get("http://cngraph.openkg.cn/#级别", [{}])[0].get("@value"),
                            "address": entry.get("http://cnschema.openkg.cn/#地址", [{}])[0].get("@value"),
                            "phone": entry.get("http://cnschema.openkg.cn/#电话号码", [{}])[0].get("@value")
                        } for entry in data if "http://www.w3.org/2000/01/rdf-schema#label" in entry}

    def check_question_and_generate_answer(question):
        can_answer = []
        cannot_answer = []

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

    all_can_answer = []
    all_cannot_answer = []

    for question in questions:
        can_answer, cannot_answer = check_question_and_generate_answer(question)
        all_can_answer.extend(can_answer)
        all_cannot_answer.extend(cannot_answer)

    with open('static/json/can_answer.json', 'w', encoding='utf-8') as can_file:
        json.dump(all_can_answer, can_file, ensure_ascii=False, indent=4)

    with open('static/json/cannot_answer.json', 'w', encoding='utf-8') as cannot_file:
        json.dump(all_cannot_answer, cannot_file, ensure_ascii=False, indent=4)

    print("检查完成，能回答和不能回答的问题已分别保存到can_answer.json和cannot_answer.json文件中。")

# 提取实体与属性
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

# 对问题进行分词
def segment_questions():
    with open('static/json/questions.json', 'r', encoding='utf-8') as f:
        list_text = json.load(f)

    segmenter = Cegmentor()
    segmentation_result = segmenter.segment(list_text)
    with open('static/json/segmentation_result.json', 'w', encoding='utf-8') as f:
        json.dump(segmentation_result, f, ensure_ascii=False, indent=4)

# 将分词结果与实体关系联系起来
def analyze_segmentation():
    with open('static/json/segmentation_result.json', 'r', encoding='utf-8') as f:
        segmentation_result = json.load(f)

    with open('static/json/extracted_entities_relationships.json', 'r', encoding='utf-8') as f:
        entities_relationships = json.load(f)

    entities = entities_relationships['entities']
    relationships = entities_relationships['relationships']

    entity_dict = {entity['label']: entity for entity in entities}

    def analyze_segmentation(segmentation_result, entity_dict, relationships):
        analysis_result = []
        for sentence in segmentation_result:
            sentence_analysis = {"tokens": sentence, "entities": [], "relationships": []}
            sentence_str = ''.join(sentence)
            for entity_label in entity_dict.keys():
                if entity_label in sentence_str:
                    sentence_analysis["entities"].append(entity_dict[entity_label])
                    for rel in relationships:
                        if rel["source"] == entity_label:
                            sentence_analysis["relationships"].append(rel)
            analysis_result.append(sentence_analysis)
        return analysis_result

    analysis_result = analyze_segmentation(segmentation_result, entity_dict, relationships)

    with open('static/json/analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=4)

    print("分析结果已存入文件 analysis_result.json")

# 评估问题的价值和难度
def evaluate_questions():
    def load_data():
        with open(r'static/json/analysis_result.json', 'r', encoding='utf-8') as f:
            analysis_result = json.load(f)
        return analysis_result

    def evaluate_question_by_entities_and_relationships(question_analysis):
        entities = question_analysis['entities']
        relationships = question_analysis['relationships']

        relevance = bool(entities)
        clarity = bool(relationships)
        informational_need = any(rel for rel in relationships if rel['relationship'] in ["类别", "级别", "地址", "电话号码", "设备"])
        practicality = informational_need

        is_valuable = relevance and clarity and informational_need and practicality
        return is_valuable

    def evaluate_question_difficulty(question_analysis):
        tokens = question_analysis['tokens']
        entities = question_analysis['entities']
        relationships = question_analysis['relationships']

        complexity = 1 if len(tokens) > 15 else 0
        knowledge_scope = 1 if entities and relationships else 0
        accuracy = 1 if any(rel for rel in relationships if rel['relationship'] in ["电话号码", "地址", "设备"]) else 0
        resources_time = 1 if len(relationships) > 3 else 0

        if any(token in tokens for token in ["是否", "是不是", "有无"]):
            difficulty_score = 1
        else:
            if any(rel for rel in relationships if rel['relationship'] in ["类别", "级别", "地址", "电话号码"]):
                difficulty_score = complexity + knowledge_scope + accuracy + resources_time - 1
            else:
                difficulty_score = complexity + knowledge_scope + accuracy + resources_time

        if not entities and not relationships:
            difficulty_score += 2

        difficulty_score = max(difficulty_score, 1)
        return difficulty_score

    def calculate_utility_ratio(is_valuable, difficulty_score, complexity, knowledge_scope, accuracy, resources_time):
        if difficulty_score == 0:
            return 0
        utility_ratio = (is_valuable + (complexity * 0.2) + (knowledge_scope * 0.3) + (accuracy * 0.3) + (resources_time * 0.2)) / difficulty_score
        return utility_ratio

    def main():
        analysis_result = load_data()
        results = []
        for question_analysis in analysis_result:
            is_valuable = evaluate_question_by_entities_and_relationships(question_analysis)
            difficulty_score = evaluate_question_difficulty(question_analysis)

            complexity = 0
            knowledge_scope = 0
            accuracy = 0
            resources_time = 0
            if len(question_analysis['tokens']) > 15:
                complexity = 1
            if question_analysis['entities'] and question_analysis['relationships']:
                knowledge_scope = 1
            if any(rel for rel in question_analysis['relationships'] if rel['relationship'] in ["电话号码", "地址", "设备"]):
                accuracy = 1
            if len(question_analysis['relationships']) > 3:
                resources_time = 1

            utility_ratio = calculate_utility_ratio(is_valuable, difficulty_score, complexity, knowledge_scope, accuracy, resources_time)
            results.append({
                "question": ' '.join(question_analysis['tokens']),
                "is_valuable": is_valuable,
                "difficulty_score": difficulty_score,
                "utility_ratio": utility_ratio,
                "entities": question_analysis['entities'],
                "relationships": question_analysis['relationships']
            })

        with open(r'static/json/evaluated_questions.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)

        print("评估结果已存入文件 evaluated_questions.json")

    if __name__ == "__main__":
        main()

# 过滤数据并生成最终文件
def filter_questions():
    with open(r'static/json/evaluated_questions.json', 'r', encoding='utf-8') as file:
        evaluated_questions = json.load(file)

    with open(r'static/json/can_answer.json', 'r', encoding='utf-8') as file:
        can_answers = json.load(file)

    def standardize_question(question):
        return question.replace(" ", "")

    answer_dict = {standardize_question(item["question"]): item["answer"] for item in can_answers}

    def generate_random_asker():
        return f"Asker{random.randint(1, 100)}"

    filtered_data_with_answers = []
    for index, item in enumerate(evaluated_questions, start=1):
        filtered_data_with_answers.append(
            {
                "tasks_id": str(index),
                "title": "",
                "content": item["question"],
                "utility": item["utility_ratio"],  
                "difficulty": item["difficulty_score"],
                "arrival_date": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
                "deadline": default_leave_time1().strftime("%Y-%m-%d %H:%M:%S %Z"),
                "assigned": False,
                "asked_by": generate_random_asker(),
                "answered_by": None,
                "answered": answer_dict.get(standardize_question(item["question"]), "No answer available") != "No answer available",
                "answer": answer_dict.get(standardize_question(item["question"]), "No answer available")
            }
        )

    with open(r'static/json/filtered_questions_with_answers.json', 'w', encoding='utf-8') as file:
        json.dump(filtered_data_with_answers, file, indent=4, ensure_ascii=False)

    print("数据已成功过滤并保存到 filtered_questions_with_answers.json 文件中。")

# 主函数
def main():
    generate_questions()
    check_questions()
    extract_entities()
    segment_questions()
    analyze_segmentation()
    evaluate_questions()
    filter_questions()

if __name__ == "__main__":
    main()
