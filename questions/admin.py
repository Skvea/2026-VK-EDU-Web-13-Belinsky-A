from django.contrib import admin
from django.db.models import Count

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('author', 'text', 'is_correct', 'rating', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author',)
    show_change_link = True


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'questions_count')
    search_fields = ('name',)
    list_filter = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_questions_count=Count('questions'))

    @admin.display(description='Количество вопросов', ordering='_questions_count')
    def questions_count(self, obj):
        return getattr(obj, '_questions_count', obj.questions.count())


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'rating', 'answers_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'text', 'author__username')
    raw_id_fields = ('author',)
    filter_horizontal = ('tags',)
    list_select_related = ('author', 'author__profile')
    inlines = [AnswerInline]
    date_hierarchy = 'created_at'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'rating', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('text', 'author__username', 'question__title')
    raw_id_fields = ('question', 'author')
    list_select_related = ('question', 'author', 'author__profile')
    date_hierarchy = 'created_at'


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'question__title')
    raw_id_fields = ('user', 'question')
    list_select_related = ('user', 'question')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'answer', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'answer__text')
    raw_id_fields = ('user', 'answer')
    list_select_related = ('user', 'answer')
