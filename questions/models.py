from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class TagManager(models.Manager):
    def popular(self):
        return self.annotate(questions_count=models.Count('questions')).order_by('-questions_count', 'name')


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Название',
    )

    objects = TagManager()

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_name': self.name})


class QuestionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('author', 'author__profile')

    def new(self):
        return self.get_queryset().prefetch_related('tags').order_by('-created_at')

    def best(self):
        return self.get_queryset().prefetch_related('tags').order_by('-rating', '-created_at')

    def by_tag(self, tag_name):
        return self.get_queryset().filter(tags__name=tag_name).prefetch_related('tags').order_by('-created_at')


class Question(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок',
    )
    text = models.TextField(
        verbose_name='Текст вопроса',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='questions',
        blank=True,
        verbose_name='Теги',
    )
    rating = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Рейтинг',
    )
    answers_count = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Количество ответов',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question', kwargs={'question_id': self.id})

    @property
    def created(self):
        return self.created_at

    def update_rating(self):
        total = self.likes.aggregate(total=models.Sum('value'))['total'] or 0
        self.rating = total
        self.save(update_fields=['rating'])
        return total

    def update_answers_count(self):
        cnt = self.answers.count()
        self.answers_count = cnt
        self.save(update_fields=['answers_count'])
        return cnt


class AnswerManager(models.Manager):
    def for_question(self, question_id):
        return self.get_queryset().filter(
            question_id=question_id,
        ).select_related('author', 'author__profile').order_by('-is_correct', '-rating', 'created_at')


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Текст ответа',
    )
    is_correct = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Правильный ответ',
    )
    rating = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Рейтинг',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
    )

    objects = AnswerManager()

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['-is_correct', '-rating', 'created_at']

    def __str__(self):
        return f'Ответ #{self.id} к вопросу "{self.question.title[:30]}"'

    @property
    def created(self):
        return self.created_at

    def update_rating(self):
        total = self.likes.aggregate(total=models.Sum('value'))['total'] or 0
        self.rating = total
        self.save(update_fields=['rating'])
        return total


class QuestionLike(models.Model):
    LIKE_CHOICES = (
        (1, 'Лайк'),
        (-1, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Пользователь',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Вопрос',
    )
    value = models.SmallIntegerField(
        default=1,
        choices=LIKE_CHOICES,
        verbose_name='Оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оценки',
    )

    class Meta:
        verbose_name = 'Лайк вопроса'
        verbose_name_plural = 'Лайки вопросов'
        unique_together = ('user', 'question')
        constraints = [
            models.UniqueConstraint(fields=['user', 'question'], name='unique_question_like'),
        ]

    def __str__(self):
        verb = 'Лайк' if self.value > 0 else 'Дизлайк'
        return f'{verb} от {self.user.username} к вопросу #{self.question_id}'


class AnswerLike(models.Model):
    LIKE_CHOICES = (
        (1, 'Лайк'),
        (-1, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='Пользователь',
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Ответ',
    )
    value = models.SmallIntegerField(
        default=1,
        choices=LIKE_CHOICES,
        verbose_name='Оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оценки',
    )

    class Meta:
        verbose_name = 'Лайк ответа'
        verbose_name_plural = 'Лайки ответов'
        unique_together = ('user', 'answer')
        constraints = [
            models.UniqueConstraint(fields=['user', 'answer'], name='unique_answer_like'),
        ]

    def __str__(self):
        verb = 'Лайк' if self.value > 0 else 'Дизлайк'
        return f'{verb} от {self.user.username} к ответу #{self.answer_id}'
