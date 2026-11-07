from django.http import Http404
from django.shortcuts import render

from core.utils import paginate

TAGS = ['black-jack', 'bender', 'python', 'perl', 'django', 'MySQL', 'TechnoPark', 'FireFox']

QUESTIONS = [
    {
        'id': i,
        'title': f'Question title {i}',
        'text': f'Text of the question {i}. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.',
        'likes': (i * 37) % 101 - 10,
        'answers_count': (i * 7) % 13,
        'tags': [TAGS[i % len(TAGS)], TAGS[(i * 3 + 1) % len(TAGS)]],
        'created': f'2026-10-{i % 28 + 1:02d}T14:25',
    }
    for i in range(1, 101)
]


def make_answers(question_id):
    return [
        {
            'id': i,
            'text': f'Answer {i} to question {question_id}. Lorem ipsum dolor sit amet, consectetuer adipiscing elit.',
            'likes': (i * 5) % 9 - 2,
            'is_correct': i == 1,
            'created': f'2026-10-{i % 28 + 1:02d}T15:02',
        }
        for i in range(1, 14)
    ]


def index(request):
    page = paginate(QUESTIONS, request, per_page=5)
    return render(request, 'questions/index.html', {'page': page, 'is_authorized': True})


def hot(request):
    hot_questions = sorted(QUESTIONS, key=lambda q: q['likes'], reverse=True)
    page = paginate(hot_questions, request, per_page=5)
    return render(request, 'questions/hot.html', {'page': page, 'is_authorized': True})


def tag(request, tag_name):
    tag_questions = [q for q in QUESTIONS if tag_name in q['tags']]
    page = paginate(tag_questions, request, per_page=5)
    return render(request, 'questions/tag.html', {
        'page': page,
        'tag_name': tag_name,
        'is_authorized': True,
    })


def question(request, question_id):
    if not 1 <= question_id <= len(QUESTIONS):
        raise Http404('Question not found')
    page = paginate(make_answers(question_id), request, per_page=3)
    return render(request, 'questions/question.html', {
        'question': QUESTIONS[question_id - 1],
        'page': page,
    })


def ask(request):
    return render(request, 'questions/ask.html', {'is_authorized': True})
