from django.apps import AppConfig
from django.contrib import admin

class AppConfigCustom(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    def ready(self):
        admin.site.site_header = "JiyashCreation"
        admin.site.site_title = "Jiyash Admin"
        admin.site.index_title = "Admin Panel"
