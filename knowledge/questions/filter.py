import json
import random
from datetime import datetime, timedelta

# 假设我们有一个时区库
from pytz import timezone

# 设定时区为 Asia/Shanghai
tz = timezone('Asia/Shanghai')

# 定义默认的截止时间函数
def default_leave_time1():
    return datetime.now(tz) + timedelta(days=7)

# 读取evaluated_questions.json文件
with open(r'static\css\json\evaluated_questions.json', 'r', encoding='utf-8') as file:
    evaluated_questions = json.load(file)

# 读取can_answer.json文件
with open(r'static\css\json\can_answer.json', 'r', encoding='utf-8') as file:
    can_answers = json.load(file)

# 创建一个标准化问题的函数
def standardize_question(question):
    return question.replace(" ", "")

# 创建一个字典，以便快速查找答案
answer_dict = {standardize_question(item["question"]): item["answer"] for item in can_answers}

# 生成随机提问者
def generate_random_asker():
    return f"Asker{random.randint(1, 100)}"

# 过滤数据，并添加answer属性，同时生成其他属性
filtered_data_with_answers = []
for index, item in enumerate(evaluated_questions, start=1):
    filtered_data_with_answers.append(
        {
            "tasks_id": str(index),
            "title": "",
            "content": item["question"],
            "utility": item["is_valuable"],  # 将is_valuable改为utility
            "difficulty": item["difficulty_score"],  # 将difficulty_score改为difficulty
            "arrival_date": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "deadline": default_leave_time1().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "assigned": False,
            "asked_by": generate_random_asker(),
            "answered_by": None,
            "answered": answer_dict.get(standardize_question(item["question"]), "No answer available") != "No answer available",
            "answer": answer_dict.get(standardize_question(item["question"]), "No answer available")
        }
    )

# 输出处理后的JSON数据
with open(r'static\css\json\filtered_questions_with_answers.json', 'w', encoding='utf-8') as file:
    json.dump(filtered_data_with_answers, file, indent=4, ensure_ascii=False)

print("数据已成功过滤并保存到 filtered_questions_with_answers.json 文件中。")
