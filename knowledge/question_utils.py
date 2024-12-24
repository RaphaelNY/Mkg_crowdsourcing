import json
import random
from datetime import datetime, timedelta
import jieba
from django.utils import timezone
# from cemotion import Cegmentor
from knowledge.models import Question
from knowledge.redis_utils import check_question_and_generate_answer

def standardize_question(question):
    return question.replace(" ", "")

def generate_random_asker():
    return f"Asker{random.randint(1, 100)}"

# 定义默认的截止时间函数
def default_leave_time1():
    return datetime.now() + timedelta(days=7)

def evaluate_question_by_entities_and_relationships(question_analysis):
        entities = question_analysis['entities']
        relationships = question_analysis['relationships']

        relevance = bool(entities)
        clarity = bool(relationships)
        informational_need = any(rel for rel in relationships if rel['relationship'] in ["类别", "级别", "地址", "电话号码", "设备"])
        practicality = informational_need

        is_valuable = relevance and clarity and informational_need and practicality
        return is_valuable

def analyze_segmentation(segmentation_result):
    with open('static/json/extracted_entities_relationships.json', 'r', encoding='utf-8') as f:
        entities_relationships = json.load(f)

    entities = entities_relationships['entities']
    relationships = entities_relationships['relationships']

    entity_dict = {entity['label']: entity for entity in entities}

    def analyze_segmentation(segmentation_result, entity_dict, relationships):
        analysis_result = []
        sentence = segmentation_result
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
    
    return analysis_result


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

def checkup_question(content, asker):
    can_or_not_answer = check_question_and_generate_answer(content)
    
    segmentation_result = list(jieba.lcut(content))
    # segmenter = Cegmentor()
    # segmentation_result = segmenter.segment(content)
    analysis_result = analyze_segmentation(segmentation_result)
    
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
    answer_dict = {standardize_question(item["question"]): item["answer"] for item in can_or_not_answer}
    
    filtered_data_with_answers = []
    for index, item in enumerate(results, start=1):
        filtered_data_with_answers.append(
            {
                "tasks_id": str(index),
                "title": "",
                "content": item["question"],
                "utility": item["utility_ratio"],  
                "difficulty": item["difficulty_score"],
                "assigned": False,
                "answered_by": None,
                "answered": False,
                "answer": answer_dict.get(standardize_question(item["question"]), "No answer available")
            }
        )
    # 创建新的 Question 对象并保存
    question = Question(
        tasks_id=filtered_data_with_answers[0]["tasks_id"],
        title=filtered_data_with_answers[0]["title"],
        content=filtered_data_with_answers[0]["content"],
        utility=filtered_data_with_answers[0]["utility"],
        difficulty=filtered_data_with_answers[0]["difficulty"],
        arrival_date=timezone.now(),
        deadline=timezone.now() + timedelta(days=7),  # 默认7天的截止时间
        assigned=False,
        answered=filtered_data_with_answers[0]["answered"],
        answer=filtered_data_with_answers[0]["answer"],
        answered_by=None,  # 初始未被回答
        asked_by=asker
    )
    question.save()
    print(f"Question {question.tasks_id} saved.")
    print(question.content)
    print(question.answer)
    print(question.answered)