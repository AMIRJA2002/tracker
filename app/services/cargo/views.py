from services.cargo.service import ArticleQueries, CarrierQueries, CreateTrackingDataForUser
from services.cargo.models import Article, Carrier, ArticleInformation
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import Http404


class ArticleAPI(APIView):
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
        article = ArticleQueries.create_one(user=request.user, data=data.validated_data)
        return Response(self.OutputSerializer(article).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=OutputSerializer)
    def get(self, request, pk=None):
        query = ArticleQueries.retrieve_one_or_list(user=request.user, pk=pk)
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


class TrackArticleAPI(APIView):
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

        # call CreateTrackingDataForUser class for provide data for user
        tracking_data_for_user = CreateTrackingDataForUser(user=request.user, number=number, carrier=carrier)
        data = tracking_data_for_user.check_article_status_and_send_data()

        article_serializer = self.ArticleSerializer(data['article']).data

        if data.get('last_weather_information'):
            response = Response(
                {
                    'article': article_serializer,
                    'last_weather_information': data['last_weather_information']
                }
            )
        else:
            article_information_serializer = self.ArticleInformationSerializer(data['travel_information'], many=True).data
            response = Response(
                {
                    'article': article_serializer,
                    'travel_information': article_information_serializer
                }
            )
        return response
