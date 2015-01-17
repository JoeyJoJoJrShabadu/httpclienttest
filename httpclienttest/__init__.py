"""Overview.
=============
To simplify unit testing of HTTP clients
"""

import unittest
import atexit
from random import randint


from functools import wraps
from socket import error


from httpserver import HttpTestServer, LIST, LAST, CLEAR, GETROUTE, CLEARROUTE


def maintain_run_state(clean):
    """
    Decorator to start and stop the server when routes are modified
    """
    def main_decorator(callback):
        def wrapper_func(self, *a, **kwargs):
            self.stop_server(clean)
            res = callback(self, *a, **kwargs)
            self.run_server()
            return res
        return wrapper_func
    return main_decorator


class Singleton(type):
    _instances = {}

    def __call__(cls, *a, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kwargs)
        return cls._instances[cls]


class HttpTests(unittest.TestCase):

    """
    Wrapper to provide functionality for modifying and running the test server
    Not this is a singleton object
    """
    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        """
        Route map should be of format
        {route: {'method': http_method, 'func': function}}
        If function is None then a default function is called
        """
        #unittest.TestCase.__init__(self, *args, **kwargs)
        self.calls = []
        self.url_map = {}
        self.proc = None

        self.call_list = {}
        self.last_call = None
        self.running = False

        atexit.register(self.stop_server, False)

        self.reset_route_map({})

    def stop_server(self, clean):
        """
        Terminate server sub process, modify run state as required
        """
        if self.proc:
            # Get the current state of the call list for reloading
            if not clean:
                call_func = getattr(self, LIST)
                self.call_list = call_func()

                last_func = getattr(self, LAST)
                self.last_call = last_func()

            self.proc.terminate()
            self.proc = None
            self.running = False
            return True
        else:
            return False

    def run_server(self):
        server = HttpTestServer(routes=self.route_map,
                                calls=self.call_list,
                                last_call=self.last_call)

        self.proc, utils, self.host, self.port = server.start()
        self.base = 'http://%s:%s' % (self.host, self.port)

        for name, details in utils.items():
            setattr(self, name, details['call_func'])

        self.running = True

    def clear_route_history(self, path, method):
        """
        Clear history for a given route
        """
        clear_func = getattr(self, CLEARROUTE)
        return clear_func(path, method)

    @maintain_run_state(True)
    def clear_routes(self):
        """
        Clear the route map
        """
        self.route_map = {}
        return True

    @maintain_run_state(True)
    def reset_route_map(self, route_map):
        """
        Reset the route map with a new map
        """
        self.route_map = route_map
        return True

    @maintain_run_state(False)
    def add_routes(self, route_map):
        """
        Add multiple routes to server from dict

        We don't want to call add_route each time as this will bounce the
        server a lot
        """
        for path in route_map.keys():
            route = self.route_map.get(path, {})
            for method in route_map[path].keys():
                route[method] = route_map[path][method]
            self.route_map[path] = route

        return True

    @maintain_run_state(False)
    def add_route(self, path, method='GET', callback=None):
        """
        Add a route to the test server
        """
        route = self.route_map.get(path, {})
        route[method] = callback
        self.route_map[path] = route

        return self.base + path, method

    @maintain_run_state(False)
    def delete_route(self, path, method):
        """
        Delete a route from the test server
        """
        if path in self.route_map.keys():
            if method in self.route_map[path].keys():
                func = self.route_map[path].pop(method)
                if len(self.route_map[path]) == 0:
                    self.route_map.pop(path)

                return True, func
        return False, None

    ############# Assertions provided to decorated functions #########
    def assertRouteCalled(self, path, method='GET', err_msg=None):
        """
        Assert that the specified route is called
        """
        msg = 'route %s - %s was not called' % (path, method)
        if err_msg:
            msg = err_msg
        req_func = getattr(self, GETROUTE)
        result = req_func(path, method)
        self.assertIsNotNone(result, msg)

    def assertCountRouteCalled(self, path, count, method='GET', err_msg=None):
        """
        Assert that the specified route is called a number of times
        """
        msg = 'route %s - %s was not called' % (path, method)
        if err_msg:
            msg = err_msg
        list_func = getattr(self, LIST)
        result = list_func()
        method_dict = result.get(path, {})
        hit_list = method_dict.get(method, [])

        self.assertTrue((len(hit_list) == count), msg)

    def assertLastRouteCallArguments(self, path, arg_dict,
                                     method='GET',
                                     err_msg=None):
        """
        Assert that the specified route is called with the correct args
        """
        msg = 'route %s - %s args were not correct' % (path, method)
        if err_msg:
            msg = err_msg
        req_func = getattr(self, GETROUTE)
        res = req_func(path, method)
        self.assertDictEqual(res['args'], arg_dict, msg)

    def assertLastRouteCallQueryString(self, path, param_dict,
                                       method='GET',
                                       err_msg=None):
        """
        Assert that the specified route is called with the correct query_string
        """
        msg = 'route %s - %s args were not correct' % (path, method)
        if err_msg:
            msg = err_msg
        req_func = getattr(self, GETROUTE)
        res = req_func(path, method)
        self.assertDictEqual(res['query_params'], param_dict, msg)


def _add_asserts(self_obj):
    """
    Add all assertions from the HttpTests instance to the test case object
    """
    ht = HttpTests()
    htattrs = dir(ht)
    asserts = filter(lambda x: x.startswith('assert'), htattrs)
    for asrt in asserts:
        if not asrt in dir(unittest.TestCase):
            setattr(self_obj, asrt, getattr(ht, asrt))


############################## Test Decorators ################################
def add_route(path, method='GET', function=None):
    """
    decorator to add routes at test execution
    """
    def main_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            self.ht = HttpTests()
            self.ht.add_route(path, method, function)
            _add_asserts(self)

            try:
                res = func(self)
            finally:
                self.ht.delete_route(path, method)
                self.ht.clear_route_history(path, method)
            return res
        return func_wrapper
    return main_decorator


def delete_route(path, method='GET'):
    """
    decorator to delete routes at test execution
    """
    def main_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            self.ht = HttpTests()
            exists, del_func = self.ht.delete_route(path, method)
            _add_asserts(self)

            try:
                res = func(self)
            finally:
                if exists:
                    self.ht.add_route(path, method, del_func)

            return res
        return func_wrapper
    return main_decorator


def add_routes(route_map):
    """
    decorator to add routes from a route map
    """
    def main_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            self.ht = HttpTests()
            self.ht.add_routes(route_map)
            _add_asserts(self)

            try:
                res = func(self)
            finally:
                for path in route_map.keys():
                    for method in route_map[path].keys():
                        self.ht.delete_route(path, method)

            return res
        return func_wrapper
    return main_decorator


def start_http():
    """
    decorator to start the server
    """
    def main_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            self.ht = HttpTests()
            _add_asserts(self)

            return func(self)
        return func_wrapper
    return main_decorator
