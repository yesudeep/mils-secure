##############################################################################
#
# Copyright 2008 Lovely Systems GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################

import types
import logging
import sys, traceback
import copy
import time

_log = logging.getLogger(__name__)

_descriptions = set(['summary', 'help', 'idempotent', 'params', 'return'])

class JSONRPCError(Exception):
    """JSONRPC Error"""

class BadJSONRequestError(Exception):
    """Cannot parse JSON-RPC request body"""

def describe_method(method):
    """Check is a callable object has description params set"""
    description = {}
    for key in _descriptions:
        if hasattr(method, key):
            description[key] = getattr(method, key)
    return description


class JSONRPCDispatcher(object):

    def __init__(self, instance=None, methods=None,
                 name='Python JSONRPC Service',
                 summary='Service dispatched by python JSONRPCDispatcher',
                 help=None, address=None, json_impl=None):

        """Initialization. Can take an instance to register upon initialization"""

        if json_impl is None:
            import simplejson
            self.json_impl = simplejson
        else:
            self.json_impl = json_impl
        self.instances = []
        self.name = name
        self.help = help
        self.address = address
        self.summary = summary
        # Store all attributes of class before any methods are added
        # for negative lookup later
        self.base_attributes = set(dir(self))
        self.base_attributes.add('base_attributes')

        # If instance was given during initialization then register it
        if instance is not None:
            self.register_instance(instance)
        if methods is not None:
            for method in methods:
                self.register_method(method)

        self.__dict__[u'system.list_methods'] = self.system_list_methods
        self.__dict__[u'system.describe'] = self.system_describe

    def get_valid_methods(self):
        valid_methods = {}
        for key, value in self.__dict__.items():
            if key.startswith('_') is False:
                if key not in self.base_attributes:
                    valid_methods[key] = value
        return valid_methods

    def register_instance(self, instance):
        """Registers all attributes of class instance to dispatcher"""
        for attribute in dir(instance):
            if attribute.startswith('_') is False:
                # All public attributes
                self.register_method(getattr(instance, attribute), name=attribute)

        # Store it in the list for convienience
        self.instances.append(instance)


    def register_method(self, function, name=None):
        """Registers a method with the dispatcher"""
        # If the name isn't passed try to find it. If we can't fail gracefully.
        if name is None:
            try:
                name = function.__name__
            except:
                if hasattr(function, '__call__'):
                    raise """Callable class instances must be passed with name parameter"""
                else:
                    raise """Not a function"""

        if self.__dict__.has_key(name) is False:
            self.__dict__[unicode(name)] = function
        else:
            print 'Attribute name conflict -- %s must be removed before attribute of the same name can be added'


    def system_list_methods(self):
        """List all the available methods and return a object parsable
        that conforms to the JSONRPC Service Procedure Description
        specification"""
        method_list = []
        for key, value in self.get_valid_methods().items():
            method = {}
            method['name'] = key
            method.update(describe_method(value))
            method_list.append(method)
        method_list.sort()
        _log.debug('system.list_methods created list %s' % str(method_list))
        return method_list

    def system_describe(self):
        """Service description"""
        description = {}
        description['sdversion'] = '1.0'
        description['name'] = self.name
        description['summary'] = self.summary
        if self.help is not None:
            description['help'] = self.help
        if self.address is not None:
            description['address'] = self.address
        description['procs'] = self.system_list_methods()
        return description

    def dispatch(self, json):
        """Public dispatcher, verifies that a method exists in it's
        method dictionary and calls it"""
        try:
            rpc_request = self._decode(json)
        except ValueError:
            raise BadJSONRequestError, json
        _log.debug('decoded to python object %s' % str(rpc_request))

        if self.__dict__.has_key(rpc_request[u'method']):
            _log.debug('dispatcher has key %s' % rpc_request[u'method'])
            return self._dispatch(rpc_request)
        else:
            _log.debug('returning jsonrpc error')
            return self._encode(result=None, error=JSONRPCError('no such method'))

    def _dispatch(self, rpc_request):
        """Internal dispatcher, handles all the error checking and
        calling of methods"""
        result = None
        error = None
        jsonrpc_id = None

        logged_failure = False

        params = rpc_request.get('params', [])
        args = []
        kwargs = {}
        if type(params) is types.DictType:
            sargs = []
            for k, v in params.items():
                k = str(k)
                try:
                    k = int(k)
                    sargs.append((k, v))
                except ValueError:
                    kwargs[k] = v
            args = [a[1] for a in sorted(sargs)]
        elif type(params) in (list, tuple):
            args =  params
        elif params is not None:
            # If type was something weird just return a JSONRPC Error
            raise JSONRPCError, 'params not array or object type'
        try:
            result = self.__dict__[rpc_request[u'method']](*args, **kwargs)
        except Exception, e:
            error = JSONRPCError('Server Exception :: %s' % e)
            error.type = e.__class__
            tb = ''.join(traceback.format_exception(*sys.exc_info()))
            logging.error(tb)

        if rpc_request.has_key('id'):
            jsonrpc_id = rpc_request[u'id']

        return self._encode(result=result, error=error, jsonrpc_id=jsonrpc_id)


    def _encode(self, result=None, error=None, jsonrpc_id=None):
        """Internal encoder method, handles error formatting, id
        persistence, and encoding via the give json_impl"""
        response = {}
        response['result'] = result
        if jsonrpc_id is not None:
            response['id'] = jsonrpc_id


        if error is not None:
            if hasattr(error, 'type'):
                error_type = str(error.type)
                error_message = str(error)
            else:
                error_type = 'JSONRPCError'
                error_message = str(error).strip()

            response['error'] = {'type':error_type,
                                 'message':error_message}
        _log.debug('serializing %s' % str(response))
        return self.json_impl.dumps(response)

    def _decode(self, json):
        """Internal method for decoding json objects, uses simplejson"""
        return self.json_impl.loads(json)

class _Method(object):

    def __init__(self, call, name, json_impl, send_id):
        self.call = call
        self.name = name
        self.json_impl = json_impl
        self.send_id = send_id

    def __call__(self, *args, **kwargs):
        # Need to handle keyword arguments per 1.1 spec
        request = {}
        request['version'] = '1.1'
        request['method'] = self.name
        if self.send_id:
            request['id'] = int(time.time())
        if len(kwargs) is not 0:
            params = copy.copy(kwargs)
            index = 0
            for arg in args:
                params[str(index)] = arg
                index = index + 1
        elif len(args) is not 0:
            params = copy.copy(args)
        else:
            params = None
        request['params'] = params
        _log.debug('Created python request object %s' % str(request))
        return self.call(self.json_impl.dumps(request))

    def __getattr__(self, name):
        return _Method(self.call, "%s.%s" % (self.name, name), self.json_impl)
