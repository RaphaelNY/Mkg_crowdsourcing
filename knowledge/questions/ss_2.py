#将segmentation_result.json 与 extracted_entities_relationships.json 联系起来，生成analysis_result.json
###

import json
from cemotion import Cegmentor

# 读取分词结果和实体关系文件
with open('static\css\json\segmentation_result.json', 'r', encoding='utf-8') as f:
    segmentation_result = json.load(f)

with open('extracted_entities_relationships.json', 'r', encoding='utf-8') as f:
    entities_relationships = json.load(f)

entities = entities_relationships['entities']
relationships = entities_relationships['relationships']

# 创建实体字典，便于快速查找
entity_dict = {entity['label']: entity for entity in entities}

# 分析分词结果，结合实体和关系信息
def analyze_segmentation(segmentation_result, entity_dict, relationships):
    analysis_result = []
    for sentence in segmentation_result:
        sentence_analysis = {"tokens": sentence, "entities": [], "relationships": []}
        sentence_str = ''.join(sentence)  # 将词组合并为字符串进行匹配
        for entity_label in entity_dict.keys():
            if entity_label in sentence_str:
                sentence_analysis["entities"].append(entity_dict[entity_label])
                # 查找相关的关系
                for rel in relationships:
                    if rel["source"] == entity_label:
                        sentence_analysis["relationships"].append(rel)
        analysis_result.append(sentence_analysis)
    return analysis_result

# 进行分析
analysis_result = analyze_segmentation(segmentation_result, entity_dict, relationships)

# 将分析结果保存到JSON文件
with open('static\css\json\analysis_result.json', 'w', encoding='utf-8') as f:
    json.dump(analysis_result, f, ensure_ascii=False, indent=4)

print("分析结果已存入文件 analysis_result.json")
