# -*- coding: utf-8 -*-
"""
    tipfy.appengine.sharded_counter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A general purpose sharded counter implementation for the datastore.

    :copyright: 2010 by tipfy.org.
    :license: Apache Software License, see LICENSE.txt for more details.
"""
import string
import random
import logging

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors

from tipfy import current_handler

#: Default configuration values for this module. Keys are:
#:
#: shards
#:     The amount of shards to use.
default_config = {
    'shards': 10,
}


class MemcachedCount(object):
    # Allows negative numbers in unsigned memcache
    DELTA_ZERO = 500000

    @property
    def namespace(self):
        return __name__ + '.' + self.__class__.__name__

    def __init__(self, name):
        self.key = 'MemcachedCount' + name

    def get_count(self):
        value = memcache.get(self.key, namespace=self.namespace)
        if value is None:
            return 0
        else:
            return string.atoi(value) - MemcachedCount.DELTA_ZERO

    def set_count(self, value):
        memcache.set(self.key, str(MemcachedCount.DELTA_ZERO + value),
            namespace=self.namespace)

    def delete_count(self):
        memcache.delete(self.key)

    count = property(get_count, set_count, delete_count)

    def increment(self, incr=1):
        value = memcache.get(self.key, namespace=self.namespace)
        if value is None:
            self.count = incr
        elif incr > 0:
            memcache.incr(self.key, incr, namespace=self.namespace)
        elif incr < 0:
            memcache.decr(self.key, -incr, namespace=self.namespace)


class Counter(object):
    """A counter using sharded writes to prevent contentions.

    Should be used for counters that handle a lot of concurrent use.
    Follows the pattern described in the Google I/O talk:
    http://sites.google.com/site/io/building-scalable-web-applications-with-google-app-engine

    Memcache is used for caching counts and if a cached count is available,
    it is the most correct. If there are datastore put issues, we store the
    un-put values into a delayed_incr memcache that will be applied as soon
    as the next shard put is successful. Changes will only be lost if we lose
    memcache before a successful datastore shard put or there's a
    failure/error in memcache.

    Example::

        # Build a new counter that uses the unique key name 'hits'.
        hits = Counter('hits')
        # Increment by 1.
        hits.increment()
        # Increment by 10.
        hits.increment(10)
        # Decrement by 3.
        hits.increment(-3)
        # This is the current count.
        my_hits = hits.count
        # Forces fetching a non-cached count of all shards.
        hits.get_count(nocache=True)
        # Set the counter to an arbitrary value.
        hits.count = 6
    """
    #: Number of shards to use.
    shards = None

    def __init__(self, name):
        self.name = name
        self.memcached = MemcachedCount('counter:' + name)
        self.delayed_incr = MemcachedCount('delayed:' + name)

    @property
    def number_of_shards(self):
        return self.shards or current_handler.app.config[__name__]['shards']

    def delete(self):
        q = db.Query(CounterShard).filter('name =', self.name)
        shards = q.fetch(limit=self.number_of_shards)
        db.delete(shards)

    def get_count_and_cache(self):
        q = db.Query(CounterShard).filter('name =', self.name)
        shards = q.fetch(limit=self.number_of_shards)
        datastore_count = 0
        for shard in shards:
            datastore_count += shard.count

        count = datastore_count + self.delayed_incr.count
        self.memcached.count = count
        return count

    def get_count(self, nocache=False):
        total = self.memcached.count
        if nocache or total is None:
            return self.get_count_and_cache()
        else:
            return int(total)

    def set_count(self, value):
        cur_value = self.get_count()
        self.memcached.count = value
        delta = value - cur_value
        if delta != 0:
            CounterShard.increment(self, incr=delta)

    count = property(get_count, set_count)

    def increment(self, incr=1, refresh=False):
        CounterShard.increment(self, incr)
        self.memcached.increment(incr)


class CounterShard(db.Model):
    name = db.StringProperty(required=True)
    count = db.IntegerProperty(default=0)

    @classmethod
    def increment(cls, counter, incr=1):
        index = random.randint(1, counter.number_of_shards)
        counter_name = counter.name
        delayed_incr = counter.delayed_incr.count
        shard_key_name = 'Shard' + counter_name + str(index)
        def get_or_create_shard():
            shard = CounterShard.get_by_key_name(shard_key_name)
            if shard is None:
                shard = CounterShard(key_name=shard_key_name, name=counter_name)
            shard.count += incr + delayed_incr
            key = shard.put()

        try:
            db.run_in_transaction(get_or_create_shard)
        except (db.Error, apiproxy_errors.Error), e:
            counter.delayed_incr.increment(incr)
            logging.error('CounterShard (%s) delayed increment %d: %s',
                          counter_name, incr, e)
            return False

        if delayed_incr:
            counter.delayed_incr.count = 0

        return True