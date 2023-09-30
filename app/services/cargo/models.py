from services.common.models import BaseModel as BUM
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Carrier(BUM):
    fullname = models.CharField(max_length=100)
    current_location = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.fullname}'


class Article(BUM):

    class Type(models.TextChoices):
        on_the_way = 'on the way',
        Delivered = 'Delivered'

    owner = models.ForeignKey(User, related_name='articles', on_delete=models.CASCADE)
    carrier = models.ForeignKey(Carrier, related_name='article', on_delete=models.DO_NOTHING, null=True, blank=True)
    name_of_article = models.CharField(max_length=100)
    number = models.PositiveBigIntegerField()
    status = models.CharField(max_length=20, choices=Type.choices, default=Type.on_the_way)

    def __str__(self):
        return f'{self.number}-{self.owner.id}'


class ArticleInformation(BUM):
    article = models.ForeignKey(Article, related_name='article_location', on_delete=models.CASCADE)
    location = models.CharField(max_length=150)
    whether_information = models.JSONField()

    def __str__(self):
        return f'{self.location}-{self.article.owner.id}'
