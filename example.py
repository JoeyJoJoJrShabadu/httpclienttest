import unittest
import requests
from httpclienttest import HttpTests, add_route, delete_route

def dummy_function(arg1, arg2):
    return 1234

class ExampleTest(unittest.TestCase):
    """
    Example testcase
    """
    
    def setUp(self):
        self.ht = HttpTests()
        self.host = self.ht.host
        self.port = self.ht.port
        
        self.base = 'http://%s/%s' % (self.host, self.port)
        
        self.req1 = '/test'
        self.req3 = '/test3'
        
        #add routes, return link
        self.call1, _ = self.ht.add_route(self.req1)
        self.ht.add_route('/test2/<arg1>/<arg2>',
                          method="POST",
                          callback=dummy_function)
        self.call3, _ = self.ht.add_route(self.req3)
        
           
    def tearDown(self):
        #Remove routes and clear call history
        self.ht.clear_routes()
        
    def test_example(self):
        requests.get(self.call1)
        requests.get(self.call1, '?key=val')
        req = requests.post(self.base + '/test2/1234/5678')
        
        params = {'key': 'val'}
        args = {'arg1': '1234', 'arg2': '5678'}
        
        #assert a get request was made to /test
        self.ht.assert_route_called(self.req1, method='GET',
                                    msg="Test route was not called")
        
        #assert two get requests were made to route /test
        self.ht.assert_count_route_called(self.req1, 2, method='GET',
                                    msg="Not called 2 times")
        
        #assert correct parameters were provided in last call to /test
        self.ht.assert_route_call_params(self.req1, params, method='GET',
                                      msg="Incorrect params")
        
        #assert correct arguments provided in call to /test2/<arg1>/<arg2>
        self.ht.assert_route_call_args(self.req2, args, method="POST",
                                       msg="Incorrect args")
        
        #Remove a route
        self.ht.delete_route(self.req3)
        
        #Call route 3 which has been removed, 404 should return
        resp = requests.get(self.call3)
        self.assertEqual(resp.status_code, 404, 'route should not exist')
        