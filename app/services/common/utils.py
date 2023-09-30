from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMessage
from django.shortcuts import Http404
import requests
import random


# open_whether_api_key
api_key = 'b8d075f52f1faa7f62328c43e438c082'


def generate_otp(length=6):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def send_otp_mail(otp, receiver):
    email = EmailMessage(
        subject='otp for warehouse',
        body=f'{otp}',
        to=[receiver],
    )
    email.send()


def randon_article_number(length=12):
    code = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return str(code)


def call_open_whether(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('Error in fetching weather data')
        raise Http404
