#根据analysis_result.json中的内容进行问题的评估，分析其有无价值及其难易程度
###

import json

def load_data():
    # 读取分词结果和实体关系文件
    with open('static\css\json\analysis_result.json', 'r', encoding='utf-8') as f:
        analysis_result = json.load(f)
    return analysis_result

def evaluate_question_by_entities_and_relationships(question_analysis):
    entities = question_analysis['entities']
    relationships = question_analysis['relationships']
    
    # 定义评估标准
    relevance = False
    clarity = False
    informational_need = False
    practicality = False
    
    # 评估相关性：是否包含特定实体
    if entities:
        relevance = True
    
    # 评估明确性：是否包含具体的关系
    if relationships:
        clarity = True
    
    # 评估信息需求：实体与关系是否展示出具体信息需求
    if any(rel for rel in relationships if rel['relationship'] in ["类别", "级别", "地址", "电话号码", "设备"]):
        informational_need = True
    
    # 评估实用性：回答这些实体和关系是否对用户有实际帮助
    if informational_need:
        practicality = True
    
    # 对问题进行最终评估
    is_valuable = relevance and clarity and informational_need and practicality
    
    return is_valuable

def evaluate_question_difficulty(question_analysis):
    tokens = question_analysis['tokens']
    entities = question_analysis['entities']
    relationships = question_analysis['relationships']
    
    # 定义难度评估标准
    complexity = 0
    knowledge_scope = 0
    accuracy = 0
    resources_time = 0
    
    # 评估复杂性：根据问题的长度和涉及的步骤来评估
    if len(tokens) > 15:
        complexity = 1
    
    # 评估知识范围：根据涉及的实体和关系类型来评估
    if entities and relationships:
        knowledge_scope = 1
    
    # 评估信息准确性：是否需要精确的数据或信息
    if any(rel for rel in relationships if rel['relationship'] in ["电话号码", "地址", "设备"]):
        accuracy = 1
    
    # 评估资源和时间：是否需要大量的资源和时间来回答
    if len(relationships) > 3:
        resources_time = 1
    
    # 检查问题是否包含“是否”这样的词
    if any(token in tokens for token in ["是否", "是不是", "有无"]):
        difficulty_score = 1
    else:
        # 检查问题是否是关于实体属性的问题
        if any(rel for rel in relationships if rel['relationship'] in ["类别", "级别", "地址", "电话号码"]):
            difficulty_score = complexity + knowledge_scope + accuracy + resources_time - 1
        else:
            # 综合评估难度
            difficulty_score = complexity + knowledge_scope + accuracy + resources_time
    
    # 如果没有实体和属性，增大难易程度
    if not entities and not relationships:
        difficulty_score += 2  # 进一步增大难易程度
    
    # 确保难度评分不低于1
    difficulty_score = max(difficulty_score, 1)
    
    return difficulty_score

def main():
    analysis_result = load_data()
    results = []
    for question_analysis in analysis_result:
        is_valuable = evaluate_question_by_entities_and_relationships(question_analysis)
        difficulty_score = evaluate_question_difficulty(question_analysis)
        results.append({
            "question": ' '.join(question_analysis['tokens']),
            "is_valuable": is_valuable,
            "difficulty_score": difficulty_score,
            "entities": question_analysis['entities'],
            "relationships": question_analysis['relationships']
        })
    
    # 将结果保存到文件
    with open('static\css\json\evaluated_questions.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print("评估结果已存入文件 evaluated_questions.json")

if __name__ == "__main__":
    main()
