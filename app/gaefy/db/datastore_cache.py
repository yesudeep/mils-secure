# -*- coding: utf-8 -*-
"""
    gaefy.db.datastore_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Provides a shim that caches datastore Get calls for a single request.
    This avoids multiple get's for the same keys in the same request, and will
    make ReferenceProperty reuse already loaded entities during the same
    request. On put, delete, the related entities cache is cleaned, and no
    cache is used during transactions.

    To use it, install and uninstall the cache in your main.py:

        from gaefy.db.datastore_cache import DatastoreCachingShim

        [...]

        def main():
            DatastoreCachingShim.Install()
            run_wsgi_app(application)
            DatastoreCachingShim.Uninstall()

    Authors:
        Nick Johnson (initial version)
        Alkis Evlogimenos (improvements, memcache version)
        Rodrigo Moraes (single-request cache version)
"""
import itertools

from google.appengine.api import apiproxy_stub_map
from google.appengine.datastore import datastore_pb

class APIProxyShim(object):
    """A generic shim class, with methods to install/uninstall it.

    Subclasses of this class can be used to replace the real stub for a service,
    intercepting and possibly passing on calls to the original stub.
    """
    # To be overridden by subclasses
    SERVICE_NAME = None
    _instance = None

    def __init__(self, wrapped_stub):
        """Constructor. Internal use only - see Install()."""
        self._wrapped_stub = wrapped_stub

    def CallWrappedStub(self, call, request, response):
        """Allows subclasses to call the wrapped stub."""
        self._wrapped_stub.MakeSyncCall(self.SERVICE_NAME, call, request,
            response)

    def MakeSyncCall(self, service, call, request, response):
        assert (service == self.SERVICE_NAME,
            'Got service name "%s", expected "%s"'
            % (service, self.SERVICE_NAME))
        messages = []
        assert request.IsInitialized(messages), messages
        method = getattr(self, '_Dynamic_' + call, None)
        if method:
            method(request, response)
        else:
            self.CallWrappedStub(call, request, response)

        assert response.IsInitialized(messages), messages

    def __getattr__(self, name):
        """Pass-through to the wrapped stub."""
        return getattr(self._wrapped_stub, name)

    @classmethod
    def Install(cls):
        """Installs the shim. Only needs to be run once at import time.

        Note that this accesses internal members of APIProxyStubMap, so may
        break in future.
        """
        if not cls._instance:
            wrapped_stub = apiproxy_stub_map.apiproxy.GetStub(cls.SERVICE_NAME)
            assert wrapped_stub, "No service '%s' found." % cls.SERVICE_NAME
            cls._instance = cls(wrapped_stub)
            stub_dict = apiproxy_stub_map.apiproxy._APIProxyStubMap__stub_map
            stub_dict[cls.SERVICE_NAME] = cls._instance

    @classmethod
    def Uninstall(cls):
        """Uninstalls the shim.

        Note that there's no need to uninstall a shim after each request. You
        can install it once at import time and leave it there between requests.
        """
        if cls._instance:
            stub_dict = apiproxy_stub_map.apiproxy._APIProxyStubMap__stub_map
            stub_dict[cls.SERVICE_NAME] = cls._instance._wrapped_stub
            cls._instance = None


class DatastoreCachingShim(APIProxyShim):
    SERVICE_NAME = 'datastore_v3'

    def __init__(self, default_stub):
        super(DatastoreCachingShim, self).__init__(default_stub)
        self.cache = {}
        self.to_delete = {}

    def GetMulti(self, encoded_keys):
        """Returns multiple entities from the local cache given a list of keys.
        """
        res = {}
        for key in encoded_keys:
            if key in self.cache:
                res[key] = self.cache[key]
        return res

    def SetMulti(self, entities_dict):
        """Sets multiple entities in the local cache given a dict of key:entity.
        """
        for key, entity in entities_dict.iteritems():
            self.cache[key] = entity
        return {}

    def DeleteMulti(self, encoded_keys):
        """Deletes multiple entities from the local cache given a list of keys.
        """
        for key in encoded_keys:
            if key in self.cache:
                del self.cache[key]
        return True

    def _Dynamic_Get(self, request, response):
        """Intercepts get requests and returns them from cache if available."""
        if request.has_transaction():
            self.CallWrappedStub('Get', request, response)
            return

        new_request = datastore_pb.GetRequest()
        new_response = datastore_pb.GetResponse()
        encoded_keys = [k.Encode() for k in request.key_list()]
        cached = self.GetMulti(encoded_keys)

        for key, encoded_key in itertools.izip(request.key_list(),
            encoded_keys):
            if encoded_key not in cached:
                new_request.add_key().CopyFrom(key)

        if new_request.key_size() > 0:
            self.CallWrappedStub('Get', new_request, new_response)

        entity_iter = iter(new_response.entity_list())
        for encoded_key in encoded_keys:
            entity = cached.get(encoded_key, None)
            if entity:
                response.add_entity().mutable_entity().CopyFrom(entity)
            else:
                entity = entity_iter.next()
                if entity.entity().IsInitialized():
                    self.cache[encoded_key] = entity.entity()
                response.add_entity().CopyFrom(entity)

    def _Dynamic_Put(self, request, response):
        """Intercepts puts and adds them to the cache."""
        self.CallWrappedStub('Put', request, response)

        # If this is in a transaction we mark these entries for deletion
        # when and if the transaction commits.
        if request.has_transaction():
            to_delete = [k.Encode() for k in response.key_list()]
            self.to_delete[request.transaction().handle()].extend(to_delete)
            return

        for e, k in itertools.izip(request.entity_list(), response.key_list()):
            e.key().CopyFrom(k)
            self.cache[k.Encode()] = e

    def _Dynamic_Delete(self, request, response):
        """Intercepts deletes and deletes entries from the cache."""
        self.CallWrappedStub('Delete', request, response)

        to_delete = [k.Encode() for k in request.key_list()]

        # If this is in a transaction we mark these entries for deletion
        # when and if the transaction commits.
        if request.has_transaction():
            self.to_delete[request.transaction().handle()].extend(to_delete)
            return

        self.DeleteMulti(to_delete)

    def _Dynamic_Next(self, request, response):
        """Intercepts query results and caches the returned entities."""
        self.CallWrappedStub('Next', request, response)
        for e in response.result_list():
            self.cache[e.key().Encode()] = e

    def _Dynamic_BeginTransaction(self, request, transaction):
        """Intercepts the beginning of transactions and creates thread local
        storage for deletions.
        """
        self.CallWrappedStub('BeginTransaction', request, transaction)
        self.to_delete[transaction.handle()] = []

    def _Dynamic_Commit(self, transaction, transaction_response):
        """Intercepts the commit of transactions and deletes all entities that
        were modified/delete by this transaction.
        """
        # We delete from cache before we commit otherwise we have a race
        # condition.
        to_delete = self.to_delete[transaction.handle()]
        if to_delete:
            self.DeleteMulti(to_delete)

        del self.to_delete[transaction.handle()]
        self.CallWrappedStub('Commit', transaction, transaction_response)

    def _Dynamic_Rollback(self, transaction, transaction_response):
        """Intercepts the rollback of transactions and clears the thread local
        storage for them.
        """
        del self.to_delete[transaction.handle()]
        self.CallWrappedStub('Rollback', transaction, transaction_response)
