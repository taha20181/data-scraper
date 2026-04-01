from django.contrib import admin

# Register your models here.
from scraper.models import Session, ScrapingLog

admin.site.register(Session)
admin.site.register(ScrapingLog)