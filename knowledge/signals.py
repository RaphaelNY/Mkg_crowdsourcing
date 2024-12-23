# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Question, Expert, Asker
from .DTA_utils import DTAAlgorithm  # 引入你的分配算法
from django.utils import timezone
from django.db.models.signals import pre_delete

# 信号处理函数 - 当用户提交问题时触发
@receiver(post_save, sender=Question)
def handle_question_submission(sender, instance, created, **kwargs):
    if created:  # 确保是新创建的问题
        print(f"New question submitted: {instance.title}")
        current_time = timezone.now()
        dta_algorithm = DTAAlgorithm(method='Greedy')  # 你可以根据需要选择不同的分配方法
        dta_algorithm.allocate_tasks(current_time)

# 信号处理函数 - 当专家完成注册时触发
@receiver(post_save, sender=Expert)
def handle_expert_registration(sender, instance, created, **kwargs):
    if created:  # 确保是新注册的专家
        print(f"New expert registered: {instance.expert_id}")
        current_time = timezone.now()
        dta_algorithm = DTAAlgorithm(method='Greedy')  # 选择分配方法
        dta_algorithm.allocate_tasks(current_time)

# 信号处理函数 - 当专家回答完问题时触发
@receiver(post_save, sender=Question)
def handle_expert_answer_submission(sender, instance, created, **kwargs):
    if instance.answered:  # 如果问题已回答
        print(f"Expert answered the question: {instance.title}")
        current_time = timezone.now()
        dta_algorithm = DTAAlgorithm(method='Greedy')  # 选择分配方法
        dta_algorithm.allocate_tasks(current_time)

@receiver(pre_delete, sender=Question)
def handle_question_deletion(sender, instance, **kwargs):
    """
    当一个问题被删除时，遍历所有专家，将该问题从他们的 assigned_tasks 和 assigned_tasks_utilities 中移除。
    """
    print(f"Question {instance.id} is being deleted. Updating experts...")
    experts = Expert.objects.filter(assigned_tasks=instance)
    for expert in experts:
        # 从 assigned_tasks 中移除问题
        expert.assigned_tasks.remove(instance)
        
        # 从 assigned_tasks_utilities 中移除相关的记录
        updated_utilities = [
            task for task in expert.assigned_tasks_utilities
            if task['task_id'] != instance.id
        ]
        expert.assigned_tasks_utilities = updated_utilities
        expert.save()
    print(f"Question {instance.id} removed from all experts.")
    
@receiver(pre_delete, sender=Expert)    
def handle_expert_deletion(sender, instance, **kwargs):
    """
    当一个专家被删除时，遍历其分配的所有问题，将问题的 assigned 属性设置为 False。
    """
    print(f"Expert {instance.expert_id} is being deleted. Updating questions...")
    assigned_questions = instance.assigned_tasks.all()
    for question in assigned_questions:
        question.assigned = False
        question.assigned_by = None  # 如果有 assigned_by 字段用于记录专家
        question.save()
    print(f"Questions previously assigned to expert {instance.expert_id} are now unassigned.")