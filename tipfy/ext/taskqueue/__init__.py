# -*- coding: utf-8 -*-
"""
    tipfy.ext.taskqueue
    ~~~~~~~~~~~~~~~~~~~

    Task queue utilities extension.

    :copyright: 2010 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
import logging
from google.appengine.ext import db

from google.appengine.ext.deferred import defer, run, PermanentTaskFailure
from google.appengine.runtime import DeadlineExceededError

from tipfy import RequestHandler


class DeferredHandler(RequestHandler):
    """A handler class that processes deferred tasks invocations, mirrored from
    `google.appengine.ext.deferred`. Map to this handler if you want to use the
    deferred package running on the same WSGI application as other handlers.
    Tipfy utilities will then be available to be used in the deferred function.

    The setup for app.yaml is:

    .. code-block:: yaml

       - url: /_ah/queue/deferred
         script: main.py
         login: admin

    The URL rule for urls.py is:

    .. code-block:: python

       Rule('/_ah/queue/deferred', endpoint='tasks/deferred',
           handler='tipfy.ext.taskqueue:DeferredHandler')
    """
    def post(self):
        headers = ['%s:%s' % (k, v) for k, v in self.request.headers.items()
               if k.lower().startswith('x-appengine-')]
        logging.info(', '.join(headers))

        try:
            run(self.request.data)
        except PermanentTaskFailure, e:
            logging.exception('Permanent failure attempting to execute task')

        return ''


class Mapper(object):
    """A base class to process all entities in single datastore kind, using
    the task queue. On each request, a batch of entities is processed and a new
    task is added to process the next batch.

    For example, to delete all 'MyModel' records:

    .. code-block:: python

       from tipfy.ext.taskqueue import Mapper
       from mymodels import myModel

       class MyModelMapper(EntityTaskHandler):
           model = MyModel

           def map(self, entity):
               # Add the entity to the list of entities to be deleted.
               return ([], [entity])

       mapper = MyModelMapper()
       deferred.defer(mapper.run)


    The setup for app.yaml is:

    .. code-block:: yaml

       - url: /_ah/queue/deferred
         script: main.py
         login: admin

    The URL rule for urls.py is:

    .. code-block:: python

       Rule('/_ah/queue/deferred', endpoint='tasks/deferred',
           handler='tipfy.ext.tasks:DeferredHandler')

    This class derives from
    http://code.google.com/appengine/articles/deferred.html
    """
    # Subclasses should replace this with a model class (eg, model.Person).
    model = None

    # Subclasses can replace this with a list of (property, value) tuples
    # to filter by.
    filters = []

    def __init__(self):
        self.to_put = []
        self.to_delete = []

    def map(self, entity):
        """Updates a single entity.

        Implementers should return a tuple containing two iterables
        (to_update, to_delete).
        """
        return ([], [])

    def finish(self):
        """Called when the mapper has finished, to allow for any final work to
        be done.
        """
        pass

    def get_query(self):
        """Returns a query over the specified kind, with any appropriate
        filters applied.
        """
        q = self.model.all()
        for prop, value in self.filters:
            q.filter('%s =' % prop, value)

        q.order('__key__')
        return q

    def run(self, batch_size=20):
        """Starts the mapper running."""
        self._continue(None, batch_size)

    def _batch_write(self):
        """Writes updates and deletes entities in a batch."""
        if self.to_put:
            db.put(self.to_put)
            self.to_put = []

        if self.to_delete:
            db.delete(self.to_delete)
            self.to_delete = []

    def _continue(self, start_key, batch_size):
        """Processes a batch of entities."""
        q = self.get_query()
        # If we're resuming, pick up where we left off last time.
        if start_key:
            q.filter('__key__ >', start_key)

        # Keep updating records until we run out of time.
        try:
            # Steps over the results, returning each entity and its index.
            for i, entity in enumerate(q):
                map_updates, map_deletes = self.map(entity)
                self.to_put.extend(map_updates)
                self.to_delete.extend(map_deletes)

                # Record the last entity we processed.
                start_key = entity.key()

                # Do updates and deletes in batches.
                if (i + 1) % batch_size == 0:
                    self._batch_write()

        except DeadlineExceededError:
            # Write any unfinished updates to the datastore.
            self._batch_write()
            # Queue a new task to pick up where we left off.
            defer(self._continue, start_key, batch_size)
            return

        # Write any updates to the datastore, since it may not have happened
        # otherwise
        self._batch_write()

        self.finish()
