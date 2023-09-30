from django.urls import path
from . import views


urlpatterns = [
    path('create/article/', views.CargoAPI.as_view(), name='create_article'),
    path('articles/', views.CargoAPI.as_view(), name='list_articles'),
    path('articles/<int:pk>/', views.CargoAPI.as_view(), name='get_article'),
    path('update/carrier/<int:pk>/', views.CarrierChangeLocationAPI.as_view(), name='update_carrier'),
    path('article/', views.TrackCargoAPI.as_view(), name='article_location'),
]
