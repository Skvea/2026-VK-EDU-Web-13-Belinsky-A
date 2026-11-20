from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


class AdminConfigTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('superadmin', 'admin@example.com', 'adminpass')
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_all_models_registered_in_admin(self):
        registered_models = site._registry.keys()
        self.assertIn(User, registered_models)
        self.assertIn(Profile, registered_models)
        self.assertIn(Tag, registered_models)
        self.assertIn(Question, registered_models)
        self.assertIn(Answer, registered_models)
        self.assertIn(QuestionLike, registered_models)
        self.assertIn(AnswerLike, registered_models)

    def test_admin_index_accessible(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Администрирование')

    def test_user_admin_has_profile_inline(self):
        user_admin = site._registry[User]
        inline_models = [inline.model for inline in user_admin.inlines]
        self.assertIn(Profile, inline_models)

    def test_question_admin_has_answer_inline(self):
        question_admin = site._registry[Question]
        inline_models = [inline.model for inline in question_admin.inlines]
        self.assertIn(Answer, inline_models)

    def test_admin_changelists(self):
        for model in [User, Profile, Tag, Question, Answer, QuestionLike, AnswerLike]:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            url = reverse(f'admin:{app_label}_{model_name}_changelist')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f'Failed on {model_name}')


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('testuser', 'user@example.com', 'mypassword123')

    def test_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Sorry, wrong login or password!')

    def test_login_post_invalid(self):
        response = self.client.post(reverse('login'), {'login': 'testuser', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry, wrong login or password!')

    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {'login': 'testuser', 'password': 'mypassword123'})
        self.assertRedirects(response, reverse('index'))
        # user should now be authenticated in session
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('index'))
        # user should no longer be authenticated
        self.assertNotIn('_auth_user_id', self.client.session)
