from random import sample, randrange

from google.appengine.ext import db

from tipfy import cached_property, url_for

URL_CHARS = 'abcdefghijkmpqrstuvwxyzABCDEFGHIJKLMNPQRST23456789'


def get_random_url_name():
    return ''.join(sample(URL_CHARS, randrange(3, 9)))


class Url(db.Model):
    # Creation date.
    created = db.DateTimeProperty(auto_now_add=True)
    # Modification date.
    updated = db.DateTimeProperty(auto_now=True)
    target = db.StringProperty(required=True)
    public = db.BooleanProperty(default=True)

    @classmethod
    def create(cls, target, name=None, public=True):
        def txn(target, name, public):
            if not name:
                while 1:
                    name = get_random_url_name()
                    if not cls.get_by_key_name(name):
                        break
            else:
                if cls.get_by_key_name(name):
                    return None

            entity = cls(key_name=name, target=target, public=public)
            entity.put()
            return name

        return db.run_in_transaction(txn, target, name, public)

    @cached_property
    def name(self):
        return self.key().name()

    @cached_property
    def short_url(self):
        return url_for('shorty/link', url_name=self.name, full=True)


def url_pager(cursor=None, limit=20):
    def get_query(cursor=None, keys_only=False):
        query = Url.all(keys_only=keys_only) \
                   .filter('public', True) \
                   .order('-created')

        if cursor:
            query.with_cursor(cursor)

        return query

    query = get_query(cursor=cursor)
    urls = query.fetch(limit)
    cursor = query.cursor()

    has_next = get_query(cursor=cursor, keys_only=True).get()
    if not has_next:
        cursor = None

    return urls, cursor
