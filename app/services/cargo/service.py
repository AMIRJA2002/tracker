from services.common.utils import randon_article_number, call_open_whether
from services.cargo.models import Article, Carrier, ArticleInformation
from django.shortcuts import get_object_or_404, Http404
from django.contrib.auth import get_user_model
from services.common.redis import RedisClient
from datetime import datetime, timedelta
from django.db.models import QuerySet
from typing import Dict

User = get_user_model()



class ArticleQueries:

    @staticmethod
    def create_one(user: User, data: Dict[str, str]) -> Article:
        number = randon_article_number()
        article = Article.objects.create(owner=user, name_of_article=data['name_of_article'], number=number)
        return article

    @staticmethod
    def retrieve_one_or_list(user: User, pk: str | None) -> QuerySet[Article] | Article:
        if pk is not None:
            return get_object_or_404(Article, owner=user, id=pk)
        return Article.objects.filter(owner=user)

    @staticmethod
    def get_article(user: User, number: int | None, carrier_name: str | None) -> Article:
        try:
            return get_object_or_404(Article, owner=user, number=number)
        except:
            return get_object_or_404(Article, owner=user, carrier__fullname=carrier_name)

    @staticmethod
    def get_article_information(article: Article) -> QuerySet[ArticleInformation]:
        return article.article_location.all()

    @staticmethod
    def get_article_last_information(article: Article) -> ArticleInformation:
        return article.article_location.all().last()


class CarrierQueries:

    @staticmethod
    def get_one_by_id(pk: int) -> Carrier:
        return get_object_or_404(Carrier, id=pk)

    @classmethod
    def update_location(cls, carrier: Carrier, location: str) -> Carrier:
        carrier.current_location = location
        carrier.save()
        cls.update_carriers_articles_location_information(carrier, location)
        return carrier

    @classmethod
    def update_carriers_articles_location_information(cls, carrier: Carrier, location: str) -> None:
        data = cls.call_open_weather_api(location)
        articles = carrier.article.filter(status='on the way')

        article_info_list = []
        for article in articles:
            article_info = ArticleInformation(location=location, article=article, whether_information=data)
            article_info_list.append(article_info)

        ArticleInformation.objects.bulk_create(article_info_list)

    @classmethod
    def call_open_weather_api(cls, location):
        open_weather = OpenWeather(str(location))
        data = open_weather.get_weather_information()
        return data


class OpenWeather:

    def __init__(self, location_name: str) -> None:
        self.location_name = location_name

    def get_weather_information(self) -> Dict[str, any]:
        redis_conn = RedisClient.new_connection()
        information = redis_conn.hgetall(self.location_name)

        if information:
            date_time = information.get('date_time')
            if self.compare_time(date_time):
                return information
            else:
                pass
        else:
            new_information = self.call_open_weather_api()
            self.store_whether_data_in_redis(data=new_information)
            return self.get_weather_information()

    def call_open_weather_api(self) -> Dict[str, any] | Http404:
        try:
            return call_open_whether(self.location_name)
        except Http404:
            raise Http404

    def store_whether_data_in_redis(self, data: Dict[str, any]) -> None:
        dict = self.select_desired_data(data)
        redis_conn = RedisClient.new_connection()

        for key, value in dict.items():
            redis_conn.hset(self.location_name, key, value)

        redis_conn.expire(self.location_name, 30)

    @classmethod
    def select_desired_data(cls, data: Dict[str, any]) -> Dict[str, str]:
        _dict = {}
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        date_time = datetime.now()
        _dict.update({'weather': weather, 'temperature': temperature, 'date_time': str(date_time)})
        return _dict

    @classmethod
    def compare_time(cls, date_time: str) -> bool:
        input_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S.%f")
        current_time = datetime.now()
        time_difference = current_time - input_time
        max_allowed_time_difference = timedelta(hours=2)

        if time_difference > max_allowed_time_difference:
            return False
        else:
            return True


class CreateTrackingDataForUser:
    def __init__(self, user: User, number: int, carrier: str) -> None:
        self.user = user
        self.number = number
        self.carrier = carrier

    def get_article(self) -> Article:
        return ArticleQueries.get_article(user=self.user, number=self.number, carrier_name=self.carrier)

    def get_article_information(self) -> QuerySet[ArticleInformation]:
        return ArticleQueries.get_article_information(article=self.get_article())

    def check_article_status_and_send_data(self) -> Dict[str, any]:
        article = self.get_article()
        article_information = self.get_article_information()
        if article.status == article.Type.Delivered:
            return self.article_with_delivered_status(article=article, article_information=article_information)
        else:
            return self.article_with_on_the_way_status(article=article)

    @classmethod
    def article_with_delivered_status(cls, article: Article, article_information: QuerySet[ArticleInformation]) -> Dict[str, any]:
        return {'article': article, 'travel_information': article_information}

    def article_with_on_the_way_status(self, article: Article) -> Dict[str, any]:
        data = self.call_open_weather(location=article.carrier.current_location)
        return {'article': article, 'last_weather_information': data}

    @classmethod
    def call_open_weather(cls, location: str) -> Dict[str, any]:
        open_weather = OpenWeather(str(location))
        data = open_weather.get_weather_information()
        data['city'] = location  # add name of coty to data
        return data
