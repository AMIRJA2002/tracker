from django.contrib import admin
from .models import Article, Carrier, ArticleInformation


@admin.register(Article)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'number', 'name_of_article', 'status')


@admin.register(Carrier)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'fullname', 'current_location')


@admin.register(ArticleInformation)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'location')
