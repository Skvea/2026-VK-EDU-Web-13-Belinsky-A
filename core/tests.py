import io
from PIL import Image

from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


def get_test_image(name='test_avatar.png'):
    file_obj = io.BytesIO()
    image = Image.new('RGB', (60, 60), color='red')
    image.save(file_obj, format='PNG')
    file_obj.seek(0)
    return SimpleUploadedFile(name, file_obj.read(), content_type='image/png')


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
        self.user.profile.nickname = 'Tester'
        self.user.profile.save()

    def test_login_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Sorry, wrong login or password!')

    def test_header_ask_button_visibility(self):
        # unauthenticated user must NOT see the Ask button
        response_unauth = self.client.get(reverse('index'))
        self.assertNotContains(response_unauth, 'class="ask-btn"')

        # authenticated user DOES see the Ask button
        self.client.force_login(self.user)
        response_auth = self.client.get(reverse('index'))
        self.assertContains(response_auth, 'class="ask-btn"')

    def test_login_post_invalid(self):
        response = self.client.post(reverse('login'), {'login': 'testuser', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry, wrong login or password!')
        # entered username should be preserved
        self.assertContains(response, 'value="testuser"')

    def test_login_post_valid(self):
        response = self.client.post(reverse('login'), {'login': 'testuser', 'password': 'mypassword123'})
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_login_with_next_param(self):
        response = self.client.post(
            f"{reverse('login')}?next=/ask/",
            {'login': 'testuser', 'password': 'mypassword123', 'next': '/ask/'}
        )
        self.assertRedirects(response, '/ask/')

    def test_login_prevents_open_redirect(self):
        response = self.client.post(
            reverse('login'),
            {'login': 'testuser', 'password': 'mypassword123', 'next': 'https://evil.com'}
        )
        self.assertRedirects(response, reverse('index'))

    def test_logout_redirects_to_referer(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('logout'), HTTP_REFERER='http://testserver/hot/')
        self.assertRedirects(response, '/hot/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_signup_success(self):
        response = self.client.post(reverse('signup'), {
            'login': 'newbie_user',
            'email': 'newbie@example.com',
            'nickname': 'Newbie',
            'password': 'StrongPassword2026',
            'password2': 'StrongPassword2026',
        })
        self.assertRedirects(response, reverse('index'))
        new_user = User.objects.get(username='newbie_user')
        self.assertEqual(new_user.email, 'newbie@example.com')
        self.assertEqual(new_user.profile.nickname, 'Newbie')
        self.assertEqual(int(self.client.session['_auth_user_id']), new_user.pk)

    def test_signup_password_mismatch(self):
        response = self.client.post(reverse('signup'), {
            'login': 'mismatch_user',
            'email': 'mismatch@example.com',
            'nickname': 'Mismatch',
            'password': 'StrongPassword2026',
            'password2': 'DifferentPassword2026',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match.')
        self.assertFalse(User.objects.filter(username='mismatch_user').exists())

    def test_signup_password_validator_failure(self):
        # 4 chars is too short (MinimumLengthValidator requires 8)
        response = self.client.post(reverse('signup'), {
            'login': 'shortpass_user',
            'email': 'short@example.com',
            'nickname': 'Short',
            'password': '123',
            'password2': '123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='shortpass_user').exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_get_prefilled_data(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'user@example.com')
        self.assertContains(response, 'Tester')

    def test_profile_post_update_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'login': 'testuser_updated',
            'email': 'updated@example.com',
            'nickname': 'Updated Tester',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Settings saved successfully!')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser_updated')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.nickname, 'Updated Tester')

    def test_profile_avatar_upload_valid(self):
        self.client.force_login(self.user)
        img = get_test_image('avatar.png')
        response = self.client.post(reverse('profile'), {
            'login': self.user.username,
            'email': self.user.email,
            'nickname': self.user.profile.nickname,
            'avatar': img,
        })
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertTrue(bool(self.user.profile.avatar))
        # ensure upload path is unguessable (hex uuid)
        self.assertIn('avatars/', self.user.profile.avatar.name)
        self.assertTrue(len(self.user.profile.avatar.name.split('/')[-1]) >= 32)

    def test_profile_avatar_upload_invalid_extension(self):
        self.client.force_login(self.user)
        # GIF is a valid image file, but disallowed extension (only jpg, jpeg, png, webp allowed)
        file_obj = io.BytesIO()
        image = Image.new('RGB', (10, 10), color='green')
        image.save(file_obj, format='GIF')
        file_obj.seek(0)
        bad_file = SimpleUploadedFile('avatar.gif', file_obj.read(), content_type='image/gif')

        response = self.client.post(reverse('profile'), {
            'login': self.user.username,
            'email': self.user.email,
            'nickname': self.user.profile.nickname,
            'avatar': bad_file,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avatar must be JPG, PNG, or WEBP.')
