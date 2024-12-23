from django.core.management.base import BaseCommand
from django.utils import timezone
from knowledge.models import Expert, Question
from django.db.models import Count,F
from knowledge.DTA_utils import DTAAlgorithm  # 导入你已定义的任务分配算法

class Command(BaseCommand):
    help = '检查并分配专家任务'

    def handle(self, *args, **kwargs):
        self.check_and_allocate_tasks()

    def check_and_allocate_tasks(self):
        current_time = timezone.now()
        
        # 检测系统中是否有专家
        if not Expert.objects.exists():
            self.stdout.write(self.style.WARNING('系统中没有专家'))
            return
        
        # 检测系统中是否有问题
        if not Question.objects.exists():
            self.stdout.write(self.style.WARNING('系统中没有问题'))
            return

        # 查找所有未满负荷的专家，通过 annotate 计算 assigned_tasks 的数量
        experts_with_unallocated_tasks = Expert.objects.annotate(
            task_count=Count('assigned_tasks')
        ).filter(
            available_until__gte=current_time,
            task_count__lt=F('max_tasks')  # 通过 task_count 进行比较
        )

        if not experts_with_unallocated_tasks.exists():
            self.stdout.write(self.style.SUCCESS('所有专家都已经分配满问题'))
            return

        # 查找所有未分配的任务
        unassigned_tasks = Question.objects.filter(assigned=False, arrival_date__lte=current_time, deadline__gte=current_time)

        if not unassigned_tasks.exists():
            self.stdout.write(self.style.SUCCESS('没有未分配的问题'))
            return

        # 如果有未分配的问题，使用DTA算法进行分配
        allocation_method = 'Greedy'  # 或者根据需要选择其他方法
        algorithm = DTAAlgorithm(method=allocation_method)
        algorithm.allocate_tasks(current_time)
        
        unassigned_tasks = Question.objects.filter(assigned=False, arrival_date__lte=current_time, deadline__gte=current_time)
        
        self.stdout.write(self.style.SUCCESS(f'{len(unassigned_tasks)} 个问题未分配'))
