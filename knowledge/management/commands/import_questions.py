import json
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from knowledge.models import Question, Asker, Expert

class Command(BaseCommand):
    help = 'Load questions from a JSON file into the database'

    def handle(self, *args, **options):
        with open('static/css/json/filtered_questions_with_answers.json', 'r', encoding='utf-8') as file:
            questions_data = json.load(file)
            for question_data in questions_data:
                # 如果 arrival_date 字段包含时区信息，确保它是标准格式
                arrival_date_str = question_data.get('arrival_date')
                if arrival_date_str:
                    # 将 CST 转换为 +08:00 或其他合适的时区
                    arrival_date_str = arrival_date_str.replace(' CST', '+08:00')
                    arrival_date = parse_datetime(arrival_date_str)
                else:
                    arrival_date = timezone.now()  # 默认使用当前时间
                    
                deadline_str = question_data.get('deadline')
                if deadline_str:
                    deadline_str = deadline_str.replace(' CST', '+08:00')
                    deadline = parse_datetime(deadline_str)
                else:
                    arrival_date = timezone.now()

                Question.objects.create(
                    tasks_id=question_data['tasks_id'],
                    title=question_data['title'],
                    content=question_data['content'],
                    utility=question_data['utility'],
                    difficulty=question_data['difficulty'],
                    arrival_date=arrival_date,
                    deadline=deadline,
                    assigned=question_data['assigned'],
                    answered=question_data['answered'],
                    answer=question_data['answer']
                )

            self.stdout.write(self.style.SUCCESS('Successfully loaded questions'))
