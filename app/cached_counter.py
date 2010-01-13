# By Bill Katz, modified from code suggested by Nick Johnson

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.api.capabilities import CapabilitySet
import logging

class Counter(db.Model):
    """A databased-backed counter."""
    count = db.IntegerProperty(default=0)
    error_possible = db.BooleanProperty(default=False)

class CachedCounter(object):
    """A memcached datastore-backed counter that handles high concurrency
       without sharding.

    Gated so won't do puts more frequently than once every UPDATE_INTERVAL
    seconds.  Also uses CapabilitySet to force non-memcached approach if
    memcached is planned to be down during update interval.

    In cases of unidirectional incrementing, e.g., a monotonically increasing
    unique ID generator, this routine is guaranteed to underestimate the true
    value in worst case failure.

    Based on App Engine Cookbook recipe: 
    "High-concurrency counters without sharding"

    Usage:
    >>> counter = CachedCounter('MyModel')
    >>> counter.incr()
    1
    >>> counter.incr()
    2
    >>> counter.count
    2
    >>> counter.incr(3)
    5
    >>> counter.count
    5
    """

    def __init__(self, name, update_interval=2):
        self._name = name
        self._lock_key = "CounterLock:%s" % (name,)
        self._incr_key = "CounterIncr:%s" % (name,)
        self._count_key = "CounterValue:%s" % (name,)
        self._update_interval = update_interval

    @property
    def count(self):
        value = memcache.get(self._count_key)
        incr = int(memcache.get(self._incr_key) or 0)
        if value is None:
            entity = Counter.get_or_insert(key_name=self._name)
            value = entity.count + incr
            memcache.set(self._count_key, value)
            return int(value)
        return int(value + incr)

    def incr(self, value=1):
        if value < 0:
            raise ValueError('CachedCounter cannot handle negative numbers.')
        def update_count(name, incr, error_possible=False):
            entity = Counter.get_by_key_name(name)
            if entity:
                entity.count += incr
                logging.debug("incr(%s): update_count on retrieved entity by %d to %d", name, incr, entity.count)
            else:
                entity = Counter(key_name=name, count=incr)
                logging.debug("incr(%s): update_count on new entity set to %d", name, incr)
            if error_possible:
                entity.error_possible = True
            entity.put()
            return entity.count

        look_ahead_time = 10 + self._update_interval
        memcache_ops = CapabilitySet('memcache', methods=['add'])
        memcache_down = not memcache_ops.will_remain_enabled_for(look_ahead_time)
        if memcache_down or memcache.add(self._lock_key, None, time=self._update_interval):
            # Update the datastore
            incr = int(memcache.get(self._incr_key) or 0) + value
            logging.debug("incr(%s): updating datastore with %d", self._name, incr)
            memcache.set(self._incr_key, 0)
            try:
                stored_count = db.run_in_transaction(update_count, self._name, incr)
            except:
                memcache.set(self._incr_key, incr)
                logging.error('Counter(%s): unable to update datastore counter.', self._name)
                raise
            memcache.set(self._count_key, stored_count)
            return stored_count
        else:
            incr = memcache.get(self._incr_key)
            if incr is None:
                # _incr_key in memcache should be set.  If not, two possibilities:
                # 1) memcache has failed between last datastore update.
                # 2) this branch has executed before memcache set in update branch (unlikely)
                stored_count = db.run_in_transaction(update_count, 
                                    self._name, value, error_possible=True)
                memcache.set(self._count_key, stored_count)
                memcache.set(self._incr_key, 0)
                logging.error('Counter(%s): possible memcache failure in update interval.',
                              self._name)
                return stored_count
            else:
                memcache.incr(self._incr_key, delta=value)
                logging.debug("incr(%s): incrementing memcache with %d", self._name, value)
                return self.count

