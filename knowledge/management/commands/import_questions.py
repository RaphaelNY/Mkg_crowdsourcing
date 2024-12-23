import json
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from knowledge.models import Question, Asker, Expert

class Command(BaseCommand):
    help = 'Load questions from a JSON file into the database'

    def handle(self, *args, **options):
        with open('static/css/json/filtered_questions_with_answers.json', 'r', encoding='utf-8') as file:
            questions_data = json.load(file)
            for question_data in questions_data:
                asked_by = Asker.objects.get(username=question_data['asked_by'])
                answered_by = None
                if question_data.get('answered_by'):
                    answered_by = Expert.objects.get(username=question_data['answered_by'])
                Question.objects.create(
                    tasks_id=question_data['tasks_id'],
                    title=question_data['title'],
                    content=question_data['content'],
                    utility=question_data['utility'],
                    difficulty=question_data['difficulty'],
                    arrival_date=parse_datetime(question_data['arrival_date']),
                    deadline=parse_datetime(question_data['deadline']),
                    assigned=question_data['assigned'],
                    asked_by=asked_by,
                    answered_by=answered_by,
                    answered=question_data['answered'],
                    answer=question_data['answer']
                )
            self.stdout.write(self.style.SUCCESS('Successfully loaded questions'))
