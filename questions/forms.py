import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'tags',
            'maxlength': '200',
            'placeholder': 'Separate tags with commas, up to 5 tags',
        }),
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'title',
                'maxlength': '255',
                'placeholder': 'Enter question title',
                'required': True,
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'text',
                'rows': '10',
                'maxlength': '5000',
                'placeholder': 'Describe your problem in detail',
                'required': True,
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise ValidationError('Title cannot be empty.')
        return title

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise ValidationError('Question text cannot be empty.')
        return text

    def clean_tags(self):
        raw_tags = self.cleaned_data.get('tags', '').strip()
        if not raw_tags:
            return []

        parts = [p.strip().lower() for p in re.split(r'[, ]+', raw_tags) if p.strip()]
        unique_tags = list(dict.fromkeys(parts))

        if len(unique_tags) > 5:
            raise ValidationError('You can add no more than 5 tags.')

        for tag_name in unique_tags:
            if len(tag_name) > 50:
                raise ValidationError(f'Tag "{tag_name}" is too long (maximum 50 characters).')

        return unique_tags

    def save(self, author=None, commit=True):
        question = super().save(commit=False)
        if author:
            question.author = author
        if commit:
            question.save()
            tag_names = self.cleaned_data.get('tags', [])
            tag_objs = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
            question.tags.set(tag_objs)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'answer-text',
                'rows': '5',
                'maxlength': '2000',
                'placeholder': 'Enter your answer here...',
                'required': True,
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise ValidationError('Answer text cannot be empty.')
        return text

    def save(self, question=None, author=None, commit=True):
        answer = super().save(commit=False)
        if question:
            answer.question = question
        if author:
            answer.author = author
        if commit:
            answer.save()
            if question:
                question.update_answers_count()
        return answer


class VoteForm(forms.Form):
    object_id = forms.IntegerField(min_value=1)
    value = forms.IntegerField()

    def clean_value(self):
        val = self.cleaned_data.get('value')
        if val not in (-1, 1):
            raise ValidationError('Vote value must be 1 or -1.')
        return val
