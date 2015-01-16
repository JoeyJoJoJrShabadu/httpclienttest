import unittest
import requests
from httpclienttest import HttpTests, add_route, delete_route, setup_http

def dummy_function(arg1, arg2):
    return 1234

class DecoratorExampleTest(unittest.TestCase):
    """
    Example testcase using decorators - provides self.ht object
    """
    @setup_http
    def test_example(self):
        self.ht.add_route('/test')
        
        requests.get(self.ht.base + '/test')
        
        self.assertRouteCalled('/test', method='GET',
                                    msg="Test route was not called")
        
        
    @add_route('/test')
    @add_route('/test2/<arg1>/<arg2>')
    @add_route('/test3')    
    def test_example2(self):
        requests.get(self.ht.base + '/test')
        requests.get(self.ht.base + '/test?key=val')
        req = requests.post(self.ht.base + '/test2/1234/5678')
        
        self.assertEqual(req.content, '1234', 'Response should be 1234')
        
        params = {'key': 'val'}
        args = {'arg1': '1234', 'arg2': '5678'}
        
        #assert a get request was made to /test
        self.assertRouteCalled('/test', method='GET',
                                    msg="Test route was not called")
        
        #assert two get requests were made to route /test
        self.assertCountRouteCalled('/test', 2, method='GET',
                                    msg="Not called 2 times")
        
        #assert correct parameters were provided in last call to /test
        self.assertLastRouteCallQueryString('/test', params, method='GET',
                                      msg="Incorrect params")
        
        #assert correct arguments provided in call to /test2/<arg1>/<arg2>
        self.assertLastRouteCallArguments('/test2', args, method="POST",
                                       msg="Incorrect args")
        
        #Remove a route
        self.ht.delete_route('/test3')
        
        #Call route 3 which has been removed, 404 should return
        resp = requests.get(self.ht.base + '/test3')
        self.assertEqual(resp.status_code, 404, 'route should not exist')

        
class DecoratorExampleTest2(unittest.TestCase):
    """
    Example testcase using decorators
    """
    
    def setUp(self):
        self.ht = HttpTests()
        self.req1 = '/test'
        
        #add routes, return link
        self.call1, _ = self.ht.add_route(self.req1)
           
    def tearDown(self):
        #Remove routes and clear call history
        self.ht.clear_routes()
    
    @delete_route('/test')
    def test_example(self):
        #Call route 3 which has been removed, 404 should return
        resp = requests.get('http://%s:%s/%s' % (self.ht.host,
                                                 self.ht.port, 
                                                 '/test'))
        
        self.assertEqual(resp.status_code, 404, 'route should not exist')