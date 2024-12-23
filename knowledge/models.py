from datetime import timedelta
from django.db import models
from django.utils import timezone


def default_leave_time1():
    return timezone.now() + timedelta(days=3)

def default_leave_time2():
    return timezone.now() + timedelta(days=2)

class NormalUser(models.Model):
    # 用户名称
    name = models.CharField(max_length=100)
    
    # 用户类型，默认值是 'inquirer'（提问者）
    USER_TYPE_CHOICES = [
        ('expert', 'Expert'),     # 专家
        ('inquirer', 'Inquirer')  # 提问者
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='inquirer')
    
    def __str__(self):
        return self.name
    
class Asker(models.Model):
    owner = models.ForeignKey(NormalUser, on_delete=models.SET_NULL, null=True)
	
class Question(models.Model):
    tasks_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    utility = models.FloatField(default=1.0)
    difficulty = models.IntegerField(default=1) # 任务难度
    
    arrival_date = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(default=default_leave_time1())
    
    assigned = models.BooleanField(default=False) # 是否分配给专家
    asked_by = models.ForeignKey(Asker, on_delete=models.CASCADE, null=True)
    answered_by = models.ForeignKey('Expert', on_delete=models.SET_NULL, null=True, blank=True)
    answered = models.BooleanField(default=False) # 是否回答
    answer = models.TextField(null=True, blank=True)  # 只有在回答后才会有内容

    def __str__(self):
        return self.content
    
class Expert(models.Model):
    owner = models.ForeignKey(NormalUser, on_delete=models.SET_NULL, null=True)
    
    expert_id = models.CharField(max_length=100, unique=True)
    max_tasks = models.IntegerField(default=3)
    skill_level = models.IntegerField(default=1)
    
    arrive_time = models.DateTimeField(default=timezone.now)
    available_until = models.DateTimeField(default=default_leave_time2())  # 使用普通函数作为默认值
    
    credibility = models.CharField(max_length=100, default="0.5")
    questionare_done = models.BooleanField(default=False)
    
    assigned_tasks = models.ManyToManyField(Question, blank=True)
    assigned_tasks_utilities = models.JSONField(default=list, null=True)
    
    def __str__(self):
        return f'Expert(id={self.expert_id}, max_tasks={self.max_tasks}, skill_level={self.skill_level}, arrival_time={self.arrive_time}, available_until={self.available_until}, credibility={self.credibility})'

    def save(self, *args, **kwargs):
            if not self.expert_id:  # 如果 expert_id 为空，则自动生成
                self.expert_id = f"EX{self.owner.id}"
            super().save(*args, **kwargs)