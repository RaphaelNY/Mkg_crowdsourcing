from django.urls import path, re_path
from . import views
from django.urls import path
from .views import register
urlpatterns = [
    path('login/', views.login_in, name='login_in'),
    path('register/', register, name='register'),
    path('expert_dashboard/', views.expert_dashboard, name='expert_dashboard'),
    path('submit_answer/', views.submit_answer, name='submit_answer'),  # 提交答案
    path('submit/', views.handle_submit, name='handleSubmit'),
    path('inquirer_dashboard/', views.inquirer_dashboard, name='inquirer_dashboard'),
    path('questionare/', views.questionare, name='questionare'),  # 显示问题页面
    path('question/details/<int:question_id>/', views.get_question_details, name='get_question_details'),
    path('search/', views.search_medical_orgs, name='search_medical_orgs'),  # 搜索 API
    re_path(r'^graph/(?P<org_id>.+)/$', views.show_graph_data, name='show_graph_data'),
]

