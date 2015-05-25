import datetime
import ujson
import requests
from requests.exceptions import MissingSchema, InvalidSchema, InvalidURL
from django.conf import settings
from django.db.models import Q
from django.db.models.loading import get_model
from django.utils.module_loading import import_string
from .models import Hook


class AllHooksDeliverer(object):
    DEFAULT_DUMP = ujson.dumps({})

    def deliver_each(self, hooks, payload=None): 
        if payload != None:
            dump = ujson.dumps(payload)
        for each in hooks:
            if payload == None:
                instance = each.content_object
                if hasattr(instance, 'get_static_payload'):
                    payload = instance.get_static_payload(each)
                    dump = ujson.dumps( payload )
                elif hasattr(instance, 'get_dynamic_payload'):
                    dump = ujson.dumps( instance.get_dynamic_payload(each) )
                else:
                    dump = self.DEFAULT_DUMP
            DELIVERER(each.target, dump)
    
    def filter_hooks(self, app_label, object_name, instance_pk, action):
        model = get_model(app_label, object_name)
        return Hook.objects.fetch(
            model=model, object_id=instance_pk, action=action
        )
    
    def after_deliver(self):
        return
            
    def deliver(self, app_label, object_name, instance_pk, action, payload=None):
        hooks = self.filter_hooks(app_label, object_name, instance_pk, action)
        if payload != None:
            self.deliver_each(hooks, payload=payload)
        else:
            self.deliver_each(hooks)
        self.after_deliver()        

deliver_all_hooks = AllHooksDeliverer().deliver


class HookDeliverer(object):
    def after_deliver(self, response):
        if response.status_code == 410:
            Hook.object.filter(target=response.url).delete()

    def deliver(self, target, payload):
        try:
            response = requests.post(target, data=payload)
        except (MissingSchema, InvalidSchema, InvalidURL) as e:
            Hook.objects.filter(target=target).delete()
        else:
            self.after_deliver(response)

deliver_hook = HookDeliverer().deliver



DELIVERER = import_string(getattr(settings, 
    "HOOK_DELIVERER", 
    "django_object_hooks.utils.deliver_hook"
))
