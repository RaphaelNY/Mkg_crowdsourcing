#对问题分词，生成segmentation_result.json
###

from cemotion import Cegmentor
import json

with open('static\css\json\questions.json', 'r', encoding='utf-8') as f: 
    list_text = json.load(f)

segmenter = Cegmentor()
segmentation_result = segmenter.segment(list_text)
with open('static\css\json\segmentation_result.json', 'w', encoding='utf-8') as f: 
    json.dump(segmentation_result, f, ensure_ascii=False, indent=4)
