# http://stackoverflow.com/questions/2719038/where-should-signal-handlers-live-in-a-django-project
from django.apps import AppConfig

class DOHConfig(AppConfig):
    name = 'django_object_hooks'
    verbose_name = "Django Object Hook"

    def ready(self):
        super(DOHConfig, self).ready()
        import signals
