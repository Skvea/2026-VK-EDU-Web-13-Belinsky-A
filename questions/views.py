from django.shortcuts import get_object_or_404, render

from core.utils import paginate
from .models import Answer, Question, Tag


def index(request):
    questions = Question.objects.new()
    page = paginate(questions, request, per_page=10)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    questions = Question.objects.best()
    page = paginate(questions, request, per_page=10)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    questions = Question.objects.by_tag(tag_name)
    page = paginate(questions, request, per_page=10)
    return render(request, 'questions/tag.html', {
        'page': page,
        'tag': tag_obj,
        'tag_name': tag_obj.name,
    })


def question(request, question_id):
    question_obj = get_object_or_404(Question, pk=question_id)
    answers = Answer.objects.for_question(question_obj.id)
    page = paginate(answers, request, per_page=5)
    return render(request, 'questions/question.html', {'question': question_obj, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
