import multiprocessing
import time
from random import randint
from requests.exceptions import ConnectionError

import json
import bottle
import requests


class TestServerUtilityApiError(Exception):

    "Server utility API was not set up correctly"

LIST = 'get_call_list'
LAST = 'get_last_call'
GETROUTE = 'get_last_route'
CLEAR = 'clear_calls'
CLEARROUTE = 'clear_calls_route'


class HttpTestServer(multiprocessing.Process):

    """
    Test Bottle server with wrappers to monitor calls and utility functions
    to query state
    """

    def __init__(self, host='localhost', port=12345,
                 routes=None,
                 calls=None,
                 last_call=None):
        multiprocessing.Process.__init__(self)

        self.host = host
        self.port = port
        self.base = 'http://%s:%s' % (host, port)

        self.route_map = routes

        if routes is None:
            self.route_map = {}

        self.calls = calls

        if calls is None:
            self.calls = {}

        self.app = bottle.default_app()

        self.last_call = last_call

        self.util_routes = {LIST: {'path': '/getcalls',
                                   'util_func': self._getcalls,
                                   'call_func': self._get_call_list},
                            LAST: {'path': '/getlast',
                                   'util_func': self._getlast,
                                   'call_func': self._get_last_call},
                            GETROUTE: {'path': '/getreq',
                                       'util_func': self._getreq,
                                       'call_func': self._get_last_request},
                            CLEAR: {'path': '/clearlist',
                                    'util_func': self._clearlist,
                                    'call_func': self._clear_calls},
                            CLEARROUTE: {'path': '/clearroute',
                                         'util_func': self._clearroute,
                                         'call_func': self._clear_route}}

        ################ util route handlers ################
    def _getlast(self):
        """
        Mapped to a Bottle route to get last call in history

        example URI::
        http://localhost:12345/getlast
        """
        return self.last_call

    def _getcalls(self):
        """
        Mapped to a Bottle route to get all calls in history

        example URI::
        http://localhost:1234/getcals
        """
        return self.calls

    def _clearroute(self):
        """
        Mapped to a bottle route to clear a routes call history
        arguments passed as query string to avoid routing issues

        example URI::
        http://localhost:12345/clearroute?path=path&method=method
        """
        msg = "Invalid request, requires params ?path=path&method=method"
        try:
            path = bottle.request.params.pop('path')
            method = bottle.request.params.pop('method')
        except KeyError:
            return bottle.HTTPResponse(body=msg, status=400)
        path = '/%s' % path

        if path in self.calls.keys() and method in self.calls[path].keys():
            self.calls[path].pop(method)
        return

    def _clearlist(self):
        """
        Mapped to a Bottle route to clear call history

        example URI::
        http://localhost:12345/clearlist
        """
        self.calls = {}

        return True

    def _getreq(self):
        """
        Mapped to a Bottle route to get latest call from a specified route

        example URI::
        http://localhost:12345/getreq/?path=blah&method=GET
        """
        msg = "Invalid request, requires params ?path=path&method=method"

        try:
            path = bottle.request.params.pop('path')
            method = bottle.request.params.pop('method')
        except KeyError:
            return bottle.HTTPResponse(body=msg, status=400)

        path = '/%s' % path

        if path in self.calls.keys() and method in self.calls[path].keys():
            return self.calls[path][method][-1]

        return None

    ############## util functions returned to caller ###########
    def _get_call_list(self):
        """
        Generate a request to get all calls from server
        """
        resp = requests.get(self.base + self.util_routes[LIST]['path'])

        if resp.status_code != 200:
            raise TestServerUtilityApiError('get history API not configured')

        try:
            return json.loads(resp.content)
        except ValueError:
            return None

    def _get_last_call(self):
        """
        Generate a request to get last call made to server
        """
        resp = requests.get(self.base + self.util_routes[LAST]['path'])

        if resp.status_code != 200:
            raise TestServerUtilityApiError('last call API not configured')

        try:
            return json.loads(resp.content)
        except ValueError:
            return None

    def _get_last_request(self, path, method):
        """
        Generate a request to get the last call for sepcific route
        """
        if path[0] == '/':
            path = path[1:]

        query_string = '?path=%s&method=%s' % (path, method)
        url = self.base + self.util_routes[GETROUTE]['path'] + query_string

        resp = requests.get(url)

        if resp.status_code != 200:
            raise TestServerUtilityApiError('last route API not configured')
        try:
            return json.loads(resp.content)
        except ValueError:
            return None

    def _clear_route(self, path, method):
        """
        Generate request to clear call history for a route
        """

        if path[0] == '/':
            path = path[1:]

        query_string = '?path=%s&method=%s' % (path, method)
        url = self.base + self.util_routes[CLEARROUTE]['path'] \
                        + query_string

        resp = requests.get(url)
        if resp.status_code != 200:
            raise TestServerUtilityApiError('clear route API not configured')

        return True

    def _clear_calls(self):
        """
        Generate request to clear call history
        """
        requests.get(self.base + self.util_routes[CLEAR]['path'])
        return True

    def _add_util_routes(self):
        """
        Add utility routes to test server, randomise name if routes taken
        """
        for detail in self.util_routes.values():
            args = detail.get('args', ())

            while detail['path'] % args in self.route_map.keys():
                detail['path'] = '/%d%s' % (randint(0, 9), detail['path'][1:])

            new_route = bottle.Route(self.app, detail['path'] % args,
                                     'GET',
                                     detail['util_func'])
            self.app.add_route(new_route)

    def build_func(self, callback=None):
        """
        Return the default function which will callback if necessary or return
        the callback itself if not callable
        """
        def default_func(*a, **kwargs):
            route = bottle.request.route
            request = {'args': kwargs,
                       'method': bottle.request.method,
                       'headers': dict(bottle.request.headers),
                       'query_params': dict(bottle.request.query),
                       'urlparts': bottle.request.urlparts,
                       'query_string': bottle.request.query_string,
                       'body': bottle.request.json}

            path_dict = self.calls.get(route.rule, {})
            method_list = path_dict.get(route.method, [])
            method_list.append(request)
            self.last_call = method_list[-1]
            path_dict[route.method] = method_list
            self.calls[route.rule] = path_dict

            if callback:
                if hasattr(callback, '__call__'):
                    return callback(*a, **kwargs)
                return callback
            return

        return default_func

    def run(self):
        """
        Build the routes then run the service
        """
        for path in self.route_map.keys():
            for method, func in self.route_map[path].items():
                new_route = bottle.Route(self.app,
                                         path,
                                         method,
                                         self.build_func(func))
                self.app.add_route(new_route)

        self._add_util_routes()
        bottle.run(app=self.app, host=self.host, port=self.port, quiet=True)

    def start(self):
        """
        Start the server
        """
        multiprocessing.Process.start(self)
        timeout = 3
        e_time = time.time() + timeout
        conn = None
        test_url = 'http://%s:%s%s' % (self.host,
                                       self.port,
                                       self.util_routes[LIST]['path'])

        while not conn:
            try:
                conn = requests.get(test_url)
            except ConnectionError:
                time.sleep(0.5)
                if time.time() >= e_time:
                    raise ConnectionError('unable to connect to test server')

        return self, self.util_routes, self.host, self.port
