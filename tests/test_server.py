import unittest
import requests

from httpclienttest import HttpTests, Singleton, add_route, add_routes, delete_route, start_http
from httpclienttest.httpserver import LIST, CLEAR, GETROUTE, LAST


def dummy(*a, **k):
    return 'dummy'

class HttpTestAddRoute(unittest.TestCase):
    """
    Test that routes are added to server correctly
    """
    
    def setUp(self):
        self.ht = HttpTests()
        self.req, _ = self.ht.add_route('/test')
        
        self.last_func = getattr(self.ht, LAST)
        self.req_func = getattr(self.ht, GETROUTE)
        self.clear_func = getattr(self.ht, CLEAR)
    
    def tearDown(self):
        self.ht.clear_routes()
        
    def test_route_added(self):
        """
        Test that a standard route is added with no method supplied
        """
        resp = requests.get(self.req)
        self.assertEqual(resp.status_code, 200, 'Route was not added correctly')
    
    def test_routes_added_params(self):
        """
        Test that routes with params are added correctly
        """
        req, _ = self.ht.add_route('/blah/<param>')
        resp = requests.get(req.replace('<param>', '12345'))
        
        self.assertEqual(resp.status_code, 200, 'Route was not added')
        
        last_call = self.last_func()
        self.assertIn('param', last_call['args'].keys(),
                      'args should contain param as key')
        self.assertIn('12345', last_call['args'].values(),
                      'args should contain 12345 as val')
        
    def test_route_added_method(self):
        """
        Test that a route with method is added correctly
        """
        req, _ = self.ht.add_route('/test2', method="DELETE")
        resp = requests.delete(req)
        
        self.assertEqual(resp.status_code, 200, 'Route was not added')
    
    def test_route_added_callback(self):
        """
        Test that a route with callback is added correctly
        """
        self.ht.add_route('/blah/<param>', callback=dummy)
        
        resp = requests.get(self.ht.base + '/blah/12345')
        
        last_call = self.last_func()
        self.assertEqual(resp.status_code, 200, 'Route was not added')
        self.assertEqual(resp.content, 'dummy', 'Unexpected return val')
        self.assertIn('param', last_call['args'].keys(),
                      'args should contain param as key')
        self.assertIn('12345', last_call['args'].values(),
                      'args should contain 12345 as val')
    
    def test_route_added_method_callback(self):
        """
        Test that a route with method and callback is added correctly
        """
        self.ht.add_route('/blah2/<param>', method='PUT', callback=dummy)
        
        resp = requests.put(self.ht.base + '/blah2/12345')
        
        last_call = self.last_func()
        self.assertEqual(resp.status_code, 200, 'Route was not added')
        self.assertEqual(resp.content, 'dummy', 'Unexpected return val')
        self.assertIn('param', last_call['args'].keys(),
                      'args should contain param as key')
        self.assertIn('12345', last_call['args'].values(),
                      'args should contain 12345 as val')
    
    def test_route_added_return_val(self):
        """
        Test that a route with a return value instead of callback is added
        """
        req, _ = self.ht.add_route('/blah3', callback='Return')
        
        resp = requests.get(req)
        
        self.assertEqual(resp.status_code, 200, 'Route was not added correctl')
        self.assertEqual(resp.content, 'Return', 'Return val incorrect')


class HttpTestDeleteRoute(unittest.TestCase):
    """
    Test that deletion of routes works correctly
    """
    
    def setUp(self):
        self.test_route = '/test'
        self.ht = HttpTests()
        self.req, self.method = self.ht.add_route(self.test_route)
        
        self.last_func = getattr(self.ht, LAST)
        self.req_func = getattr(self.ht, GETROUTE)
        self.clear_func = getattr(self.ht, CLEAR)
    
    def tearDown(self):
        self.ht.clear_routes()
    
    def test_delete_route(self):
        """
        Test that route is deleted correctly
        """
        self.ht.delete_route(self.test_route, self.method)
        resp = requests.get(self.req)
        msg = 'route %s has not been removed' % self.test_route
        self.assertEqual(resp.status_code, 404, msg)


class HttpTestDecorators(unittest.TestCase):
    """
    Test that decorating functions work
    """
    @add_route('/test2')
    @add_route('/test3')
    def test_decorator_add(self):
        """Test the add route decorator works"""
        self.last_func = getattr(self.ht, LAST)
        
        resp = requests.get(self.ht.base + '/test3')
        self.assertEqual(resp.status_code, 200, 'route was not added')
        
        resp = requests.get(self.ht.base + '/test2')
        self.assertEqual(resp.status_code, 200, 'route was not added')
        
        last_call = self.last_func()
        self.assertEqual(last_call['urlparts']['path'], '/test2')
    
    @add_routes({'/test2': {'GET': None},
                 '/test3': {'GET': 'Return val'}})
    def test_decorator_add_routes(self):
        """Test the add routes decorators works"""
        self.last_func = getattr(self.ht, LAST)
        
        resp = requests.get(self.ht.base + '/test3')
        self.assertEqual(resp.status_code, 200, 'route was not added')
        self.assertEqual(resp.content, 'Return val')
        
        resp = requests.get(self.ht.base + '/test2')
        self.assertEqual(resp.status_code, 200, 'route was not added')
        last_call = self.last_func()
        self.assertEqual(last_call['urlparts']['path'], ['/test2'],
                         'Route not called')
        
    @add_route('/blah2/<param>', 'PUT', dummy)
    def test_decorator_add_method_func(self):
        """Ensure decorator adds function callbacks"""
        last_func = getattr(self.ht, LAST)
        resp = requests.put(self.ht + '/blah2/12345')
        last_call = last_func()
        self.assertEqual(resp.status_code, 200, 'route was not added')
        self.assertEqual(resp.content, 'dummy')
        self.assertIn('param', last_call['args'].keys(),
                      'args should contain param as key')
        self.assertIn('12345', last_call['args'].values(),
                      'args should contain 12345 as val')
    
    @start_http()
    def test_decorator_start(self):
        """Test the start clean decorator works"""
        self.assertTrue(self.ht)
        self.assertEqual(self.ht.__class__, HttpTests)
        

class HttpTestDecoratorsDelete(unittest.TestCase):
    """
    Ensure that routes are deleted correctly
    """
    def setUp(self):
        self.ht = HttpTests()
        self.test_route = '/test'
        self.req, _ = self.ht.add_route(self.test_route)
    
    @delete_route('/test', 'GET')
    def test_decorator_delete(self):
        """Test the delte route decorator works"""
        resp = requests.get(self.req)
        msg = 'route %s has not been removed' % self.test_route
        self.assertEqual(resp.status_code, 404, msg)
    