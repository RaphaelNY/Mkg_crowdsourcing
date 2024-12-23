import random
from datetime import timedelta
from django.utils import timezone
from .models import Question, Expert
from django.db.models import Avg


class DTAAlgorithm:
	def __init__(self, method):
		self.method = method

	def allocate_tasks(self, current_time):
		if self.method == 'Greedy':
			return self._greedy_allocation(current_time)
		elif self.method == 'Basic-Threshold':
			return self._basic_threshold_allocation(current_time)
		elif self.method == 'Maximum-Utility':
			return self._maximum_utility_allocation(current_time)
		elif self.method == 'Weighted-Random':
			return self._weighted_random_allocation(current_time)
		else:
			raise ValueError('Unsupported allocation method')

	def _greedy_allocation(self, current_time):
		# 获取符合条件的可用任务
		available_tasks = Question.objects.filter(arrival_date__lte=current_time, deadline__gte=current_time, assigned=False)

		# 将 QuerySet 转换为列表，以便支持 shuffle
		unallocated_tasks = list(available_tasks)

		while unallocated_tasks:
			# 随机打乱任务顺序
			random.shuffle(unallocated_tasks)
			
			new_unallocated_tasks = []
			
			# 遍历所有未分配的任务
			for task in unallocated_tasks:
				allocated = False
				# 遍历所有可用专家
				for expert in Expert.objects.filter(available_until__gte=current_time):
					if self._assign_task_to_expert(task, expert, current_time):
						allocated = True
						break  # 一旦任务分配给专家，跳出专家循环
				if not allocated:
					new_unallocated_tasks.append(task)
			
			# 如果没有任务分配成功，则退出循环
			if len(new_unallocated_tasks) == len(unallocated_tasks):
				break
			
			# 更新未分配任务列表
			unallocated_tasks = new_unallocated_tasks

	def _basic_threshold_allocation(self, current_time):
		# Basic threshold allocation with lowered threshold
		available_tasks = Question.objects.filter(arrival_date__lte=current_time, deadline__gte=current_time, assigned=False)
		threshold = available_tasks.aggregate(Avg('utility'))['utility__avg'] * 0.5 if available_tasks else 0  # Lower the threshold to 50% of mean utility
		unallocated_tasks = [task for task in available_tasks if task.utility >= threshold]
		while unallocated_tasks:
			random.shuffle(unallocated_tasks)
			new_unallocated_tasks = []
			for task in unallocated_tasks:
				allocated = False
				for expert in Expert.objects.filter(available_until__gte=current_time):
					if self._assign_task_to_expert(task, expert, current_time):
						allocated = True
						break
				if not allocated:
					new_unallocated_tasks.append(task)
			if len(new_unallocated_tasks) == len(unallocated_tasks):
				# No task was allocated, break the loop
				break
			unallocated_tasks = new_unallocated_tasks

	def _maximum_utility_allocation(self, current_time):
		# Allocate tasks based on maximum utility first
		available_tasks = Question.objects.filter(arrival_date__lte=current_time, deadline__gte=current_time, assigned=False)
		available_tasks = available_tasks.order_by('-utility')  # Sort tasks by utility
		for task in available_tasks:
			for expert in Expert.objects.filter(available_until__gte=current_time):
				if self._assign_task_to_expert(task, expert, current_time):
					break

	def _weighted_random_allocation(self, current_time, max_attempts=1000):
		# Weighted random allocation based on utility
		available_tasks = Question.objects.filter(arrival_date__lte=current_time, deadline__gte=current_time, assigned=False)
		total_utility = sum(task.utility for task in available_tasks)
		if total_utility == 0:
			return
		attempts = 0
		while available_tasks and attempts < max_attempts:
			attempts += 1
			weights = [task.utility / total_utility for task in available_tasks]
			task = random.choices(available_tasks, weights=weights, k=1)[0]
			allocated = False
			for expert in Expert.objects.filter(available_until__gte=current_time):
				if self._assign_task_to_expert(task, expert, current_time):
					allocated = True
					break
			if allocated:
				available_tasks.remove(task)
				total_utility -= task.utility
			else:
				# If task cannot be allocated, consider it for later attempts
				continue
            
	def _assign_task_to_expert(self, task, expert, current_time):
		# Check if task can be assigned to this expert
		if ((task.arrival_date <= expert.available_until) and \
			expert.assigned_tasks.count() < expert.max_tasks and \
			expert.skill_level >= task.difficulty and not task.assigned):
			# Adjust utility based on expert's credibility
			adjusted_utility = task.utility * float(expert.credibility)

			# Add the task to the expert's list of assigned tasks
			expert.assigned_tasks.add(task)

			# Store the adjusted utility in the list
			expert.assigned_tasks_utilities.append({'task_id': task.id, 'utility': adjusted_utility})
			
			# Mark the task as assigned and associate the expert with the task
			task.assigned = True
			task.assigned_by = expert  # Associate the expert with the task

			task.save()
			expert.save()

			return True
		return False

