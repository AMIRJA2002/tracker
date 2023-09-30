from celery import shared_task
from services.common.utils import send_otp_mail


@shared_task()
def send_otp_mail_celery(otp, receiver):
    send_otp_mail(otp, receiver)
