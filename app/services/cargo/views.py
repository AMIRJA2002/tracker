from services.cargo.service import CargoQueries, CarrierQueries, OpenWeather
from services.cargo.models import Article, Carrier, ArticleInformation
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import Http404


class CargoAPI(APIView):
    permission_classes = (IsAuthenticated,)

    class InputSerializer(serializers.Serializer):
        name_of_article = serializers.CharField(max_length=50)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Article
            fields = '__all__'

    @extend_schema(request=InputSerializer, responses=OutputSerializer)
    def post(self, request):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        cargo = CargoQueries.create_one(user=request.user, data=data.validated_data)
        return Response(self.OutputSerializer(cargo).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=OutputSerializer)
    def get(self, request, pk=None):
        query = CargoQueries.retrieve_one_or_list(user=request.user, pk=pk)
        if pk is not None:
            return Response(self.OutputSerializer(query).data, status=status.HTTP_200_OK)
        return Response(self.OutputSerializer(query, many=True).data, status=status.HTTP_200_OK)


class CarrierChangeLocationAPI(APIView):
    permission_classes = (IsAuthenticated,)


    class InputSerializer(serializers.Serializer):
        location = serializers.CharField(max_length=200)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Carrier
            fields = '__all__'

    @extend_schema(request=InputSerializer, responses=OutputSerializer)
    def patch(self, request, pk):
        data = self.InputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        carrier = CarrierQueries.get_one_by_id(pk=pk)
        updated_location = CarrierQueries.update_location(carrier=carrier, location=data.validated_data['location'])
        return Response(self.OutputSerializer(updated_location).data, status=status.HTTP_202_ACCEPTED)


class TrackCargoAPI(APIView):
    permission_classes = (IsAuthenticated,)

    class InputSerializer(serializers.Serializer):
        number = serializers.IntegerField(required=False)
        carrier = serializers.CharField(required=False)

    class ArticleSerializer(serializers.ModelSerializer):
        class Meta:
            model = Article
            fields = '__all__'

    class ArticleInformationSerializer(serializers.ModelSerializer):
        class Meta:
            model = ArticleInformation
            exclude = ('updated_at', 'id', 'article')

    @extend_schema(request=InputSerializer)
    def get(self, request):
        ser_data = self.InputSerializer(data=request.data)
        ser_data.is_valid(raise_exception=True)

        number = ser_data.validated_data.get('number', None)
        carrier = ser_data.validated_data.get('carrier', None)

        if not number and not carrier:  # check if carrier and number is None
            raise Http404('you must provide a number or carrier')

        article = CargoQueries.get_cargo(user=request.user, number=number, carrier_name=carrier)
        article_information = CargoQueries.get_cargo_information(cargo=article)

        if article.status == article.Type.Delivered:  # return all travel information is status is delivered
            article = self.ArticleSerializer(article).data
            location = self.ArticleInformationSerializer(article_information, many=True).data,
            response = Response({'cargo': article, 'travel_information': location})

        elif article.status != article.Type.Delivered:  # return last travel information is status is not delivered
            location = article.carrier.current_location
            article = self.ArticleSerializer(article).data
            open_weather = OpenWeather(str(location))
            data = open_weather.get_weather_information()
            data['city'] = location
            response = Response({'article': article, 'last_weather_information': data})

        return response
