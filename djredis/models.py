from functools import partial
from django.db import models

from redish.client import Client
from redish import serialization


# override and divide and balance with settings?
# db = Client(host="localhost", port=6379, db="") # default settings.
#db = Client()
db = Client(serializer=serialization.Pickler())
#db_json = Client(serializer=serialization.JSON())


#####
#Incr/Decr
###########
def _get_incr(key):
    def get_incr_value(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return int(db.api.get(full_key)) if db.api.get(full_key) else None
    return get_incr_value

def _incr(key):
    def incr(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.api.incr(full_key)
    return incr

def _decr(key):
    def decr(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.api.decr(full_key)
    return decr

def _save_incr(key, persist_field):
    def redis_save(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        value = int(db.api.get(full_key)) if db.api.get(full_key) else None
        setattr(self, persist_field, value)
        self.save()
    return redis_save

#####
#String
#############

def _get_string(key):
    def get(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.api.get(full_key)
    return get

def _append_string(key):
    def append(self, value):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.api.append(full_key, value)
    return append

def _exists_string(key):
    def exists(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.api.exists(full_key)
    return exists

def _save_string(key, persist_field):
    def redis_save(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        value = db.api.get(full_key) if db.api.get(full_key) else ''
        setattr(self, persist_field, value)
        self.save()
    return redis_save


####
#Object
#########

def _get_object(key):
    def get(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        if db.api.get(full_key):
            return db[full_key]
        else:
            return None
    return get

def _set_object(key):
    def set(self, value):
        full_key = '%s:%s' % (self.redis_key(), key)
        db[full_key] = value
        #return value
    return set

####
#List
#######

def _get_list(key):
    def get_list(self):
        full_key = '%s:%s' % (self.redis_key(), key)
        return db.List(full_key)
    return get_list

def _lpush(key):
    def lpush(self, value):
        full_key = '%s:%s' % (self.redis_key(), key)
        db.List(full_key).appendleft(value)
        return db.List(full_key)
    return lpush

def _rpush(key):
    def rpush(self, value):
        full_key = '%s:%s' % (self.redis_key(), key)
        db.List(full_key).append(value)
        return db.List(full_key)
    return rpush


class DredisMixin(object):
    '''Mixin class to go with models.Model

    ex::

        class C(models.Model, DredisMixin):
            ...
            # optionally add your own key
            def redis_key(self):
                return 'unique_space:%s' % (self.id)

        C.add_incr(C, 'timesfavorited')

        >>> c = C()
        >>> c.timesfavorited_incr()
        1
        >>> c.timesfavorited()
        1
        >>> c.timesfavorited_decr()
        0
    '''

    def redis_key(self):
        return '%s:%s:%s' % (self._meta.app_label, self._meta.module_name, self.id)

    @classmethod
    def add_incr(cls, key, persist_field=None):
        cls.add_to_class(key, _get_incr(key))
        cls.add_to_class('%s_incr' % key, _incr(key))
        cls.add_to_class('%s_decr' % key, _decr(key))
        if persist_field:
            cls.add_to_class('%s_save' % key, _save_incr(key, persist_field))

    @classmethod
    def add_string(cls, key, persist_field=None):
        cls.add_to_class(key, _get_string(key))
        cls.add_to_class('%s_append' % key, _append_string(key))
        cls.add_to_class('%s_exists' % key, _exists_string(key))
        if persist_field:
            cls.add_to_class('%s_save' % key, _save_string(key, persist_field))

    @classmethod
    def add_object(cls, key):
        cls.add_to_class(key, _get_object(key))
        cls.add_to_class('%s_set' % key, _set_object(key))

    @classmethod
    def add_list(cls, key):
        cls.add_to_class(key, _get_list(key))
        cls.add_to_class('%s_lpush' % key, _lpush(key))
        cls.add_to_class('%s_rpush' % key, _rpush(key))


