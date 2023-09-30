from services.users.service import send_otp_and_set_cache, login_user
from services.users.service import UserQueries
from django.core.exceptions import BadRequest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.http import Http404

User = get_user_model()


class TestUserQueries(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='amir8177@gmail.com', password='123456')

    def test_get_one_correct(self):
        user = self.user
        self.assertEqual(user, UserQueries.get_one(id=user.id))

    def test_get_one_incorrect(self):
        user = self.user
        with self.assertRaises(Http404):
            UserQueries.get_one(id=user.id + 1)

    def test_get_one_by_email_correct(self):
        user = self.user
        self.assertEqual(user, UserQueries.get_one_by_email(email=user.email))

    def test_get_one_by_email_incorrect(self):
        with self.assertRaises(Http404):
            UserQueries.get_one_by_email(email='amir@asa.com')

    def test_validate_user_email_correct_code(self):
        user = self.user
        send_otp_and_set_cache(user.email)
        code = cache.get(user.email)
        user = UserQueries.validate_user_email(user.email, code)
        self.assertTrue(user.is_active)

    def test_validate_user_email_incorrect_code(self):
        user = self.user
        send_otp_and_set_cache(user.email)
        with self.assertRaises(BadRequest):
            UserQueries.validate_user_email(user.email, '1421')


class TestLogin(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='amir8177@gmail.com', password='123456')

    def test_login_user(self):
        data = {'email': 'amir8177@gmail.com', 'password': '123456'}
        user = login_user(data)
        self.assertEqual(self.user, user)
        self.assertEqual(self.user.email, user.email)
        self.assertEqual(self.user.password, user.password)
