from datetime import timedelta
from django.utils import timezone
from django.conf import settings
import urllib
from django.db import transaction
from knowledge.DTA_utils import DTAAlgorithm
from knowledge.models import NormalUser, Asker, Expert, Question
from .redis_utils import get_graph_data_for_org, get_medical_org_by_id, get_medical_orgs_by_category, get_graph_data, get_medical_orgs_by_field
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
def register(request):
    if request.method == 'POST':
        user_name = request.POST.get('username', '')
        email = request.POST.get('email', '')
        pwd = request.POST.get('password', '')
        user_type = request.POST.get('user_type', 'inquirer')  # 获取用户类型，默认为提问者
        
        # 检查用户名是否已存在
        if User.objects.filter(username=user_name).exists():
            # 如果用户名已经存在，返回注册页面并显示错误信息
            return render(request, 'knowledge/login.html', {'error': True, 'msg': '重复的用户名'})

        # 创建 User 实例
        user = User.objects.create_user(username=user_name, password=pwd, email=email)
        user.save()

        # 创建 NormalUser 实例
        normal_user = NormalUser(name=user_name, user_type=user_type)
        normal_user.save()

        # 创建 Asker 或 Expert 实例
        if user_type == 'inquirer':
            Asker.objects.create(owner=normal_user)
        elif user_type == 'expert':
            Expert.objects.create(owner=normal_user)

        return render(request, 'knowledge/login.html', {'success': True, 'show_login': True})

    return render(request, 'basic/register.html')

def login(request):
    return  render(request, 'knowledge/login.html')

def expert_dashboard(request):
    if request.user.is_authenticated:
        normal_user = request.user
        # 获取当前登录用户的专家信息
        ownername = NormalUser.objects.get(name=normal_user)
        expert = Expert.objects.get(owner=ownername)
        assigned_questions = expert.assigned_tasks.all()  # 获取所有分配的任务

        context = {
            'expert': expert,  # 将专家信息传递到模板
            'assigned_questions': assigned_questions,  # 将分配的任务传递到模板
        }
        return render(request, 'knowledge/expert_dashboard.html', context)  # 专家专属页面

def inquirer_dashboard(request):
    if request.user.is_authenticated:
        normal_user = request.user
        ownername = NormalUser.objects.get(name=normal_user)
        asker = Asker.objects.get(owner=ownername)
        questions = Question.objects.filter(asked_by=asker)

        context = {
            'asker': asker,
            'questions': questions,
        }
    return render(request, 'knowledge/inquirer_dashboard.html', context)  # 提问者专属页面

@login_required
def handle_submit(request):
    if request.method == 'POST':
        content = request.POST.get('content')  # 获取表单中问题的内容
        if content:
            normal_user = request.user
            ownername = NormalUser.objects.get(name=normal_user)
            asker = Asker.objects.get(owner=ownername)

            # 创建新的 Question 对象并保存
            question = Question(
                content=content,
                arrival_date=timezone.now(),
                deadline=timezone.now() + timedelta(days=3),  # 默认3天的截止时间
                asked_by=asker
            )
            question.save()

    return redirect('inquirer_dashboard')

def get_question_details(request, question_id):
    try:
        # 获取指定id的问题
        question = Question.objects.get(id=question_id)
        # 返回问题的相关信息
        data = {
            'description': question.content,
            'id': question.id,
        }
        return JsonResponse(data)  # 返回json格式的响应
    except Question.DoesNotExist:
        return JsonResponse({'error': '问题不存在'}, status=404)  # 返回404状态码

def login_in(request):
    if request.method == 'GET':
        return render(request, 'knowledge/login.html')

    elif request.method == 'POST':
        user_name = request.POST.get('username')
        pwd = request.POST.get('password')

        user = authenticate(username=user_name, password=pwd)

        if user:
            if user.is_active:
                auth_login(request, user)

                # 获取对应的 NormalUser 实例
                normal_user = NormalUser.objects.get(name=user_name)

                # 根据用户类型跳转到不同的页面
                if normal_user.user_type == 'expert':
                    expert = Expert.objects.get(owner=normal_user)
                    if not expert.questionare_done:
                        return redirect('../questionare/')
                    else:
                        expert.available_until = timezone.now() + timedelta(days=3)
                        expert.save()
                        return redirect('../expert_dashboard/')  # 跳转到专家页面
                elif normal_user.user_type == 'inquirer':
                    return redirect('../inquirer_dashboard/')  # 跳转到提问者页面
            else:
                return render(request, 'knowledge/login.html', {'login_failed': True, 'msg': '用户未激活'})
        else:
            return render(request, 'knowledge/login.html', {'login_failed': True, 'msg': '账户名或密码错误，请重新登录'})

    return JsonResponse({'code': 405, 'msg': '方法不允许'}, status=405)

def logout_(request):
	logout(request)
	return redirect('/accounting/login')


from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist


def submit_answer(request):
    if request.method == 'POST':
        # 获取当前登录用户
        normal_user = request.user

        # 获取当前登录用户的专家信息
        try:
            ownername = NormalUser.objects.get(name=normal_user)
            expert = Expert.objects.get(owner=ownername)
        except NormalUser.DoesNotExist or Expert.DoesNotExist:
            return JsonResponse({'error': 'User or Expert not found'}, status=404)

        # 获取提交的答案和问题ID
        answer_text = request.POST.get('answer')
        question_id = request.POST.get('question_id')

        # 获取问题对象
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return JsonResponse({'error': 'Question not found'}, status=404)

        # 检查问题是否已经回答
        if question.answered:
            return JsonResponse({'error': 'This question has already been answered'}, status=400)

        # 保存答案
        question.answer = answer_text
        question.answered = True
        question.answered_by = expert

        # 从专家的 assigned_tasks 和 assigned_tasks_utilities 中移除该问题及效用值
        if question in expert.assigned_tasks.all():
            # 移除问题本身
            expert.assigned_tasks.remove(question)

            # 移除与该问题关联的效用值
            expert.assigned_tasks_utilities = [
                utility for utility in expert.assigned_tasks_utilities
                if utility.get('task_id') != question.id
            ]
            expert.save()

        # 更新专家的可信度
        utility = question.utility
        difficulty = question.difficulty
        current_credibility = float(expert.credibility)
        # 计算可信度增长值
        credibility_increase = utility / (difficulty + 1)/10

        # 更新专家的可信度，最大值为 1.0
        expert.credibility = min(1.0, current_credibility + credibility_increase)

        # 使用事务确保一致性
        with transaction.atomic():
            # 保存问题和专家的更新
            question.save()
            expert.save()

        # 跳转回专家页面
        return redirect('expert_dashboard')

    return JsonResponse({'error': 'Invalid request'}, status=400)


def medical_org_detail(request, org_id):
    """
    获取单个医疗机构详情
    """
    data = get_medical_org_by_id(org_id)
    if not data:
        return JsonResponse({"error": "Medical organization not found"}, status=404)
    return JsonResponse(data)

def medical_orgs_by_category(request, category):
    """
    获取特定类别的医疗机构列表
    """
    data = get_medical_orgs_by_category(category)
    return JsonResponse(data, safe=False)

def graph_data(request):
    """
    获取知识图谱中的图数据
    """
    data = get_graph_data()
    return JsonResponse(data, safe=False)

def medical_org_detail(request, org_id):
    data = get_medical_org_by_id(org_id)
    if not data:
        return render(request, "404.html", {"message": "Medical organization not found"})
    return render(request, "medical_org_detail.html", {"data": data})

def medical_org_detail(request, org_id):
    """
    渲染医疗机构详情页面
    """
    data = get_medical_org_by_id(org_id)
    if not data:
        return render(request, "404.html", {"message": "医疗机构未找到"})
    return render(request, "medical_org_detail.html", {"data": data})

def category_list(request):
    """
    渲染医疗机构类别列表页面
    """
    categories = ["医院", "诊所", "药店"]  # 假设类别是静态的或从 Redis 中获取
    return render(request, "category_list.html", {"categories": categories})


@csrf_exempt
def search_medical_orgs(request):
    """
    处理搜索请求，支持根据 name、level、address、phone、category 查询。
    """
    if request.method == 'GET':
        # 获取用户的搜索字段和查询值
        search_field = request.GET.get('field', '')
        search_value = request.GET.get('value', '')
        print(search_field, search_value)

        if not search_field or not search_value:
            return JsonResponse({'error': 'Missing field or value parameters'}, status=400)

        # 从 Redis 获取对应的医疗机构数据
        try:
            orgs = get_medical_orgs_by_field(search_field, search_value)
            print("Found orgs:", orgs)
        except Exception as e:
            return JsonResponse({'error': f'Error fetching data: {str(e)}'}, status=500)

        # 返回医疗机构列表
        return JsonResponse({'orgs': orgs})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def show_graph_data(request, org_id):
    """
    获取指定医疗机构的图数据，并渲染在页面上
    """
    try:
        decoded_org_id = urllib.parse.unquote(org_id)  # 正确解码 org_id
        print("Fetching graph data for org:", decoded_org_id)
        graph_data = get_graph_data_for_org(decoded_org_id)
        if not graph_data:
            return JsonResponse({'error': 'No data found for this organization'}, status=404)

        # 调试日志

        # 返回数据给前端
        graph_json = {'nodes': graph_data}
        return JsonResponse(graph_json)

    except Exception as e:
        print("Error fetching graph data:", str(e))
        return JsonResponse({'error': f'Error fetching graph data: {str(e)}'}, status=500)














from django.shortcuts import render, redirect
import json
import random
import os
import jieba

def em_algorithm(questions, user_answers, max_iter=10, tolerance=1e-4):
    # 初始化可信度
    theta = 0.5  # 初始可信度，假设为0.5

    def e_step(questions, user_answers, theta):
        """
        E步：分词并计算每个问题的回答匹配的概率
        """
        probabilities = []
        for i, question in enumerate(questions):
            correct_answer = question['answer']
            user_answer = user_answers[i]


            # 使用jieba对正确答案和用户答案进行分词
            correct_answer_words = set(jieba.cut(correct_answer))
            user_answer_words = set(jieba.cut(user_answer))

            # 计算分词后的交集（匹配的部分）
            intersection = correct_answer_words.intersection(user_answer_words)

            # 计算匹配的概率，匹配的单词越多，可信度越高
            match_probability = len(intersection) / len(correct_answer_words) if len(correct_answer_words) > 0 else 0

            # 根据匹配的程度调整概率
            probabilities.append(match_probability * theta + (1 - match_probability) * (1 - theta))

        return probabilities

    def m_step(probabilities, user_answers):
        """
        M步：根据E步的概率计算新的可信度theta
        """
        correct_count = 0
        for i, prob in enumerate(probabilities):
            # 如果用户的答案匹配正确答案，增加可信度
            if user_answers[i] == questions[i]['answer']:
                correct_count += prob

        # 更新theta为加权平均值
        theta = correct_count / len(questions)
        return theta

    # 迭代执行E步和M步
    for iteration in range(max_iter):
        # 计算E步：更新每个问题的响应概率
        probabilities = e_step(questions, user_answers, theta)

        # 计算M步：根据E步的概率更新theta
        new_theta = m_step(probabilities, user_answers)

        # 检查收敛：如果theta变化很小，则停止迭代
        if abs(new_theta - theta) < tolerance:
            break

        theta = new_theta

    return theta


def questionare(request):

    # 读取文件内容
    with open(r"C:\Users\86131\Desktop\question.json", "r", encoding="utf-8") as file:
        questions_data = json.load(file)



    # 随机抽取 15 个问题
    selected_questions = random.sample(questions_data, 15)

    if request.method == 'POST':
        # 获取用户提交的答案
        user_answers = request.POST.getlist('answers')  # 假设用户答案的名称是 'answers'

        # 使用 EM 算法计算用户的可信度
        credibility = em_algorithm(selected_questions, user_answers)

        # 保存可信度到 Expert 模型中
        if request.user.is_authenticated:
            normal_user = request.user
            ownername = NormalUser.objects.get(name=normal_user)
            try:
                expert = Expert.objects.get(owner=ownername)
                expert.credibility = credibility  # 更新可信度
                expert.skill_level = calculate_skill_level_from_credibility(credibility)  # 根据可信度计算技能等级
                expert.questionare_done = True  # 标记已完成问卷
                expert.save()
                
                current_time = timezone.now()
                dta_algorithm = DTAAlgorithm(method='Greedy')  # 你可以根据需要选择不同的分配方法
                dta_algorithm.allocate_tasks(current_time)
            except Expert.DoesNotExist:
                pass  # 如果专家记录不存在，则忽略


        return redirect('expert_dashboard')

    # 渲染问题页面
    return render(request, 'knowledge/questionare.html', {'questions': selected_questions})

def calculate_skill_level_from_credibility(credibility):
    """
    根据专家的可信度生成技能等级（分段映射）

    参数：
        credibility (float): 专家的可信度，范围在 0.0 到 1.0 之间。

    返回值：
        skill_level (int): 生成的技能等级，范围在 1 到 10 之间。
    """
    # 验证可信度
    if credibility < 0.0 or credibility > 1.0:
        raise ValueError("Credibility must be a value between 0.0 and 1.0")

    # 分段映射
    if credibility < 0.2:
        return 1
    elif credibility < 0.4:
        return 2
    elif credibility < 0.6:
        return 3
    elif credibility < 0.8:
        return 4
    elif credibility < 1.0:
        return 5
    else:
        return 6
