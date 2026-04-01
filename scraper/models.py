from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class Session(models.Model):

    SESSION_TYPE_CHOICES = [
        ('session', 'Session'),
        ('poster', 'Poster'),
    ]

    session_title = models.CharField(max_length=1000, blank=True, default='')
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default='session',
        db_index=True,
    )
    poster_abstract_title = models.TextField(blank=True, null=True, default='')
    authors = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    affiliations = models.TextField(blank=True, null=True, default='')
    date = models.CharField(max_length=100, blank=True, null=True, default='')
    time = models.CharField(max_length=100, blank=True, null=True, default='')
    location = models.CharField(max_length=100, blank=True, null=True, default='')
    session_category = models.CharField(max_length=100, blank=True, null=True, default='')
    presentation_type = models.CharField(max_length=100, blank=True, null=True, default='')
    description = models.CharField(max_length=1000, blank=True, null=True, default='')

    source_url = models.URLField(max_length=2000, blank=True, null=True, default='')
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.id} - {self.session_title}'


class ScrapingLog(models.Model):

    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')

    def __str__(self):
        return f'{self.id} - {self.status}'
