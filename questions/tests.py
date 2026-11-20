from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


class ModelAndManagerTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('alice', 'alice@example.com', 'password')
        self.user2 = User.objects.create_user('bob', 'bob@example.com', 'password')

        self.tag_python = Tag.objects.create(name='python')
        self.tag_django = Tag.objects.create(name='django')

        self.q1 = Question.objects.create(
            title='Question 1',
            text='Text 1',
            author=self.user1,
            rating=10,
        )
        self.q1.tags.add(self.tag_python)

        self.q2 = Question.objects.create(
            title='Question 2',
            text='Text 2',
            author=self.user2,
            rating=50,
        )
        self.q2.tags.add(self.tag_python, self.tag_django)

    def test_profile_creation(self):
        self.assertTrue(hasattr(self.user1, 'profile'))
        self.assertEqual(str(self.user1.profile), 'alice')

    def test_question_managers(self):
        # new questions
        new_qs = list(Question.objects.new())
        self.assertEqual(new_qs[0].id, self.q2.id)

        # best questions
        best_qs = list(Question.objects.best())
        self.assertEqual(best_qs[0].id, self.q2.id)
        self.assertEqual(best_qs[1].id, self.q1.id)

        # by_tag
        django_qs = list(Question.objects.by_tag('django'))
        self.assertEqual(len(django_qs), 1)
        self.assertEqual(django_qs[0].id, self.q2.id)

    def test_popular_tags(self):
        pop_tags = list(Tag.objects.popular())
        # python has 2 questions, django has 1
        self.assertEqual(pop_tags[0].name, 'python')
        self.assertEqual(pop_tags[1].name, 'django')

    def test_question_like_unique_together(self):
        QuestionLike.objects.create(user=self.user1, question=self.q1, value=1)
        with self.assertRaises(IntegrityError):
            QuestionLike.objects.create(user=self.user1, question=self.q1, value=1)

    def test_answer_like_unique_together(self):
        ans = Answer.objects.create(question=self.q1, author=self.user2, text='Ans')
        AnswerLike.objects.create(user=self.user1, answer=ans, value=1)
        with self.assertRaises(IntegrityError):
            AnswerLike.objects.create(user=self.user1, answer=ans, value=1)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('tester', 'tester@example.com', 'password')
        self.tag = Tag.objects.create(name='web')
        self.question = Question.objects.create(
            title='Test Question',
            text='What is web?',
            author=self.user,
            rating=5,
        )
        self.question.tags.add(self.tag)
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.user,
            text='Web is the Internet.',
            is_correct=True,
        )

    def test_index_view(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Question')

    def test_hot_view(self):
        response = self.client.get(reverse('hot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Question')

    def test_tag_view_success(self):
        response = self.client.get(reverse('tag', kwargs={'tag_name': 'web'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Question')

    def test_tag_view_404(self):
        response = self.client.get(reverse('tag', kwargs={'tag_name': 'nonexistent_tag_xyz'}))
        self.assertEqual(response.status_code, 404)

    def test_question_view_success(self):
        response = self.client.get(reverse('question', kwargs={'question_id': self.question.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Question')
        self.assertContains(response, 'Web is the Internet.')

    def test_question_view_404(self):
        response = self.client.get(reverse('question', kwargs={'question_id': 999999}))
        self.assertEqual(response.status_code, 404)

    def test_empty_state_questions(self):
        Question.objects.all().delete()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No questions yet.')

    def test_empty_state_answers(self):
        Answer.objects.all().delete()
        response = self.client.get(reverse('question', kwargs={'question_id': self.question.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No answers yet for this question.')
