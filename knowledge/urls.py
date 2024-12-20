from django.urls import path
from . import views
from django.urls import path
from .views import register
urlpatterns = [
    path('login/', views.login_in, name='login_in'),
    path('register/', register, name='register'),
    path('expert_dashboard/', views.expert_dashboard, name='expert_dashboard'),
    path('submit_answer/', views.submit_answer, name='submit_answer'),  # 提交答案
    path('inquirer_dashboard/', views.inquirer_dashboard, name='inquirer_dashboard'),
    path('questionare/', views.questionare, name='questionare'),  # 显示问题页面

]

