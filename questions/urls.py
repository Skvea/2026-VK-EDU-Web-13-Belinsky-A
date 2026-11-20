from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('api/vote/question/', views.vote_question, name='vote_question'),
    path('api/vote/answer/', views.vote_answer, name='vote_answer'),
    path('api/answer/correct/', views.mark_correct, name='mark_correct'),
]
