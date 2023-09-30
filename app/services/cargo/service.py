from services.common.utils import randon_cargo_number, call_open_whether
from services.cargo.models import Article, Carrier, ArticleInformation
from django.shortcuts import get_object_or_404, Http404
from django.contrib.auth import get_user_model
from services.common.redis import RedisClient
from datetime import datetime, timedelta
from django.db.models import QuerySet
from typing import Dict

User = get_user_model()


class CargoQueries:

    @staticmethod
    def create_one(user: User, data: Dict[str, str]) -> Article:
        number = randon_cargo_number()
        cargo = Article.objects.create(owner=user, name_of_cargo=data['name_of_article'], number=number)
        return cargo

    @staticmethod
    def retrieve_one_or_list(user: User, pk: str | None) -> QuerySet[Article] | Article:
        if pk is not None:
            return get_object_or_404(Article, owner=user, id=pk)
        return Article.objects.filter(owner=user)

    @staticmethod
    def get_cargo(user: User, number: int | None, carrier_name: str | None) -> Article:
        try:
            return get_object_or_404(Article, owner=user, number=number)
        except:
            return get_object_or_404(Article, owner=user, carrier__fullname=carrier_name)

    @staticmethod
    def get_cargo_information(cargo: Article) -> QuerySet[ArticleInformation]:
        return cargo.article_location.all()

    @staticmethod
    def get_cargo_last_information(cargo: Article) -> ArticleInformation:
        return cargo.article_location.all().last()


class CarrierQueries:

    @staticmethod
    def get_one_by_id(pk: int) -> Carrier:
        return get_object_or_404(Carrier, id=pk)

    @classmethod
    def update_location(cls, carrier: Carrier, location: str) -> Carrier:
        carrier.current_location = location
        carrier.save()
        cls.update_carriers_cargos_location_information(carrier, location)
        return carrier

    @classmethod
    def update_carriers_cargos_location_information(cls, carrier: Carrier, location: str) -> None:
        data = cls.call_open_weather_api(location)
        articles = carrier.article.filter(status='on the way')

        cargo_info_list = []
        for article in articles:
            cargo_info = ArticleInformation(location=location, article=article, whether_information=data)
            cargo_info_list.append(cargo_info)

        ArticleInformation.objects.bulk_create(cargo_info_list)

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
