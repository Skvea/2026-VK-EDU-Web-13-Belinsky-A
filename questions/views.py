from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.utils import paginate
from .forms import AnswerForm, QuestionForm, VoteForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag


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
    form = AnswerForm(request.POST or None)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if form.is_valid():
            answer = form.save(question=question_obj, author=request.user)
            answers_qs = Answer.objects.for_question(question_obj.id)
            ids = list(answers_qs.values_list('id', flat=True))
            try:
                index_pos = ids.index(answer.id)
            except ValueError:
                index_pos = len(ids) - 1
            page_num = (index_pos // 5) + 1
            return redirect(f"{question_obj.get_absolute_url()}?page={page_num}#answer-{answer.id}")

    answers = Answer.objects.for_question(question_obj.id)
    page = paginate(answers, request, per_page=5)
    return render(request, 'questions/question.html', {
        'question': question_obj,
        'page': page,
        'form': form,
    })


@login_required(login_url='login')
def ask(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_obj = form.save(author=request.user)
            return redirect(question_obj.get_absolute_url())
    else:
        form = QuestionForm()

    return render(request, 'questions/ask.html', {'form': form})


@require_POST
def vote_question(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required', 'message': 'Log in to vote.'}, status=401)

    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'invalid_data', 'errors': form.errors}, status=400)

    question_obj = get_object_or_404(Question, pk=form.cleaned_data['object_id'])
    val = form.cleaned_data['value']

    like, created = QuestionLike.objects.get_or_create(
        user=request.user,
        question=question_obj,
        defaults={'value': val},
    )
    if not created:
        if like.value == val:
            like.delete()
            user_vote = 0
        else:
            like.value = val
            like.save(update_fields=['value'])
            user_vote = val
    else:
        user_vote = val

    rating = question_obj.update_rating()
    return JsonResponse({'success': True, 'rating': rating, 'user_vote': user_vote})


@require_POST
def vote_answer(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required', 'message': 'Log in to vote.'}, status=401)

    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'invalid_data', 'errors': form.errors}, status=400)

    answer_obj = get_object_or_404(Answer, pk=form.cleaned_data['object_id'])
    val = form.cleaned_data['value']

    like, created = AnswerLike.objects.get_or_create(
        user=request.user,
        answer=answer_obj,
        defaults={'value': val},
    )
    if not created:
        if like.value == val:
            like.delete()
            user_vote = 0
        else:
            like.value = val
            like.save(update_fields=['value'])
            user_vote = val
    else:
        user_vote = val

    rating = answer_obj.update_rating()
    return JsonResponse({'success': True, 'rating': rating, 'user_vote': user_vote})


@require_POST
def mark_correct(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'auth_required', 'message': 'Log in required.'}, status=401)

    answer_id = request.POST.get('answer_id')
    answer_obj = get_object_or_404(Answer.objects.select_related('question'), pk=answer_id)

    if answer_obj.question.author != request.user:
        return JsonResponse({
            'error': 'forbidden',
            'message': 'Only question author can select correct answer.',
        }, status=403)

    answer_obj.is_correct = not answer_obj.is_correct
    answer_obj.save(update_fields=['is_correct'])

    return JsonResponse({'success': True, 'is_correct': answer_obj.is_correct})
