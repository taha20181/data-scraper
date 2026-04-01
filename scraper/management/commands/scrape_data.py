
from django.core.management.base import BaseCommand
from scraper.models import Session, ScrapingLog
from django.utils import timezone


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['sessions', 'posters', 'all'],
            default='all',
            help='What to scrape (default: all)',
        )
    
    def handle(self, *args, **options):
        scrape_type = options['type']
    
        log = ScrapingLog.objects.create(
                status='running',
            )
        
        sessions_data = []
        posters_data = []

        try:
            from scraper.action.scraper import ScrapeSchedule, ScrapePoster
            if scrape_type == 'sessions':
                data = ScrapeSchedule().execute()
                print(len(data))
            elif scrape_type == 'posters':
                data = ScrapePoster().execute()
                print(len(data))
            else:
                sessions_data = ScrapeSchedule().execute()
                posters_data = ScrapePoster().execute()
                data = sessions_data + posters_data
                print(len(data))
        except Exception as exc:
            print("Error scraping sessions:", exc)
            log.status = 'failed'
            log.completed_at = timezone.now()
            log.save()
            return

        for sessions in data:
            for record in sessions:
                try:
                    Session.objects.create(**record)
                except Exception as exc:
                    print("Error saving session record:", exc)

        log.status = 'completed'
        log.completed_at = timezone.now()
        log.save()
