from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from services.common.utils import generate_otp
from django.core.exceptions import BadRequest
from .tasks import send_otp_mail_celery
from django.core.cache import cache
from django.http import Http404
from typing import Dict

User = get_user_model()


class UserQueries:

    @classmethod
    def get_one(cls, id: int) -> User:
        return get_object_or_404(User, id=id)

    @classmethod
    def get_one_by_email(cls, email: str) -> User:
        return get_object_or_404(User, email=email)

    @classmethod
    def get_all(cls,):
        pass

    @classmethod
    def filter_many(cls, filter):
        pass

    @classmethod
    def create_one(cls, email: str, password: str) -> User:
        user = User.objects.create_user(email=email, password=password)
        user.is_active = False
        user.save()
        return user

    @classmethod
    def delete_one(cls, request):
        pass

    @classmethod
    def validate_user_email(cls, email: str, otp: str) -> User:
        code = cache.get(email)
        if code:
            if code == otp:
                user = cls.get_one_by_email(email=email)
                if user:
                    cache.delete(email)
                    user.is_active = True
                    user.save()
                    return user
                raise Http404
            raise BadRequest('code is wrong!')
        raise BadRequest('code is expired!')

    @classmethod
    def check_user_is_active(cls, email: str) -> str:
        user = User.objects.get(email=email)
        if user.is_active is False:
            return email
        raise BadRequest('this user has active account')


def login_user(data: Dict[str, str]) -> User:
    user = UserQueries.get_one_by_email(email=data.get('email'))
    if user:
        if user.check_password(data.get('password')):
            return user
        raise BadRequest('username or password is wrong')
    raise Http404


def send_otp_and_set_cache(email: str) -> None:
    otp = generate_otp()
    cache.set(email, otp), cache.expire(email, 120)
    send_otp_mail_celery.delay(otp=otp, receiver=email)
    print_otp_pretty(otp)


def print_otp_pretty(otp: str) -> None:
    print(20 * '*#', 2*'\n',)
    print('\t', f'your code is: {otp}')
    print(2*'\n', 20 * '#*')

