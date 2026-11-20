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


class AskAndAnswerFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user('author', 'author@example.com', 'password123')
        self.other_user = User.objects.create_user('other', 'other@example.com', 'password123')
        self.question = Question.objects.create(
            title='Existing Question',
            text='Existing question body text.',
            author=self.author,
        )

    def test_ask_requires_login(self):
        response = self.client.get(reverse('ask'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('ask')}")

    def test_ask_post_valid_creates_question_and_tags(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('ask'), {
            'title': 'How to use Docker with Django?',
            'text': 'I want to deploy my Django app using docker compose.',
            'tags': 'docker, django, postgres',
        })
        new_q = Question.objects.get(title='How to use Docker with Django?')
        self.assertRedirects(response, new_q.get_absolute_url())
        self.assertEqual(new_q.author, self.author)
        self.assertEqual(new_q.tags.count(), 3)
        self.assertTrue(new_q.tags.filter(name='docker').exists())

    def test_ask_post_invalid_too_many_tags(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('ask'), {
            'title': 'Test title',
            'text': 'Test text body',
            'tags': 't1, t2, t3, t4, t5, t6',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You can add no more than 5 tags.')
        self.assertFalse(Question.objects.filter(title='Test title').exists())

    def test_post_answer_unauthorized_redirects_to_login(self):
        response = self.client.post(
            reverse('question', kwargs={'question_id': self.question.id}),
            {'text': 'Unauthorized answer'}
        )
        self.assertRedirects(response, f"{reverse('login')}?next={self.question.get_absolute_url()}")
        self.assertEqual(self.question.answers.count(), 0)

    def test_post_answer_authorized_creates_answer(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse('question', kwargs={'question_id': self.question.id}),
            {'text': 'Here is the working solution.'}
        )
        self.question.refresh_from_db()
        self.assertEqual(self.question.answers_count, 1)
        new_answer = self.question.answers.first()
        self.assertIn(f'#answer-{new_answer.id}', response.url)
        self.assertEqual(new_answer.author, self.other_user)


class AjaxInteractionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user('author', 'author@example.com', 'password123')
        self.voter = User.objects.create_user('voter', 'voter@example.com', 'password123')
        self.question = Question.objects.create(
            title='Sample Question',
            text='Sample text',
            author=self.author,
            rating=0,
        )
        self.answer = Answer.objects.create(
            question=self.question,
            author=self.voter,
            text='Sample answer',
            rating=0,
            is_correct=False,
        )

    def test_vote_question_unauthorized(self):
        response = self.client.post(reverse('vote_question'), {'object_id': self.question.id, 'value': 1})
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data.get('error'), 'auth_required')

    def test_vote_question_authorized_upvote_and_cancel(self):
        self.client.force_login(self.voter)
        # 1. Upvote
        response = self.client.post(reverse('vote_question'), {'object_id': self.question.id, 'value': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['rating'], 1)
        self.assertEqual(data['user_vote'], 1)

        # 2. Clicking same vote cancels it
        response2 = self.client.post(reverse('vote_question'), {'object_id': self.question.id, 'value': 1})
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2['rating'], 0)
        self.assertEqual(data2['user_vote'], 0)

    def test_vote_answer_authorized(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('vote_answer'), {'object_id': self.answer.id, 'value': 1})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['rating'], 1)

    def test_mark_correct_unauthorized(self):
        response = self.client.post(reverse('mark_correct'), {'answer_id': self.answer.id})
        self.assertEqual(response.status_code, 401)

    def test_mark_correct_by_non_author_forbidden(self):
        # voter is NOT the author of the question
        self.client.force_login(self.voter)
        response = self.client.post(reverse('mark_correct'), {'answer_id': self.answer.id})
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data['error'], 'forbidden')
        self.answer.refresh_from_db()
        self.assertFalse(self.answer.is_correct)

    def test_mark_correct_by_author_success(self):
        # author OF THE QUESTION toggles correct
        self.client.force_login(self.author)
        response = self.client.post(reverse('mark_correct'), {'answer_id': self.answer.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_correct'])
        self.answer.refresh_from_db()
        self.assertTrue(self.answer.is_correct)

        # Toggle back
        response2 = self.client.post(reverse('mark_correct'), {'answer_id': self.answer.id})
        self.assertEqual(response2.status_code, 200)
        self.assertFalse(response2.json()['is_correct'])
