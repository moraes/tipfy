# -*- coding: utf-8 -*-
"""
    tipfy.ext.tasks
    ~~~~~~~~~~~~~~~

    Task queue utilities extension.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
from google.appengine.ext import db
from google.appengine.api.labs import taskqueue
from google.appengine.ext.deferred import run, PermanentTaskFailure

from tipfy import local, url_for, RequestHandler


class DeferredHandler(RequestHandler):
    """A handler class that processes deferred tasks invocations, mirrored from
    `google.appengine.ext.deferred`. Map to this handler if you want to use the
    deferred package running on the same WSGI application as other handlers.
    Tipfy utilities will then be available to be used in the deferred function.

    The setup for app.yaml is:

        - url: /_ah/queue/deferred
          script: main.py
          login: admin

    The URL rule for urls.py is:

        Rule('/_ah/queue/deferred', endpoint='tasks/deferred',
            handler='tipfy.ext.tasks:DeferredHandler')
    """
    use_middlewares = False

    def post(self):
        headers = ['%s:%s' % (k, v) for k, v in local.request.headers.items()
               if k.lower().startswith('x-appengine-')]
        logging.info(', '.join(headers))

        try:
            run(local.request.data)
        except PermanentTaskFailure, e:
            logging.exception('Permanent failure attempting to execute task')

        return local.response


class EntityTaskHandler(RequestHandler):
    """A base class to process all entities in single datastore kind, using
    the task queue. On each request, an entity is processed and a new task is
    added to process the next entity.

    For example, to process all 'MyModel' records:

        class MyModelTasks(EntityTaskHandler):
            model = MyModel
            endpoint = 'tasks/mymodel'

            def process_entity(self, entity, retry_count):
                # do something with current entity...
                # ...

                # Return True to process next, using 0 as countdown.
                return (True, 0)

    A couple of URL rules with a 'key' argument are required:

        Rule('/_tasks/process-mymodel/', endpoint='tasks/mymodel',
            handler='somemodule.MyModelTasks')
        Rule('/_tasks/process-mymodel/<string:key>', endpoint='tasks/mymodel',
            handler='somemodule.MyModelTasks')
    """
    use_middlewares = False
    model = None
    endpoint = None

    def get(self, **kwargs):
        return self.post(**kwargs)

    def post(self, **kwargs):
        if self.model is None or self.endpoint is None:
            raise ValueError('Model or endpoint is not defined.')

        model_class = self.model.__class__
        entity = self.get_entity(kwargs.get('key', None))
        if not entity:
            logging.info('Finished all %s entities!' % model_class)
            return local.response

        # Process current entity.
        logging.info('Processing %s from %s' % (str(entity.key()), model_class))
        retry_count = int(local.request.headers.get(
            'X-AppEngine-TaskRetryCount', 0))
        current_key = str(entity.key())
        process_next, countdown = self.process_entity(entity, retry_count)

        if process_next is True:
            # Process next entity.
            taskqueue.add(url=url_for(self.endpoint, key=current_key),
                countdown=countdown)

        return local.response

    def get_entity(self, key):
        query = self.model.all().order('__key__')
        if key:
            query.filter('__key__ >', db.Key(key))

        return query.get()

    def process_entity(self, entity, retry_count):
        """Process an entity and returns a tuple (process_next, countdown). If
        process_next is True, a new task is added to process the next entity.
        """
        return (False, 0)
