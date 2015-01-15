httpclienttest - HTTP Client testing library
********************************

httpclienttest simplifies unit testing of HTTP clients written in Python.

httpclienttest allows for one line creation of a dummy Bottle server with
configurable routes and utility functionality to easily test that requests
are being generated correctly, and responses are being parsed as expected.

Example usage:
.. code-block:: python
   emphasize-lines: 24-28,44,48,52,56,60
   
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
        
Usage with decorators:
.. code-block:: python
   :emphasize-lines: 12,22-24

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
        
        self.ht.assert_route_called('/test', method='GET',
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
        self.ht.assert_route_called('/test', method='GET',
                                    msg="Test route was not called")
        
        #assert two get requests were made to route /test
        self.ht.assert_count_route_called('/test', 2, method='GET',
                                    msg="Not called 2 times")
        
        #assert correct parameters were provided in last call to /test
        self.ht.assert_route_call_params('/test', params, method='GET',
                                      msg="Incorrect params")
        
        #assert correct arguments provided in call to /test2/<arg1>/<arg2>
        self.ht.assert_route_call_args('/test2', args, method="POST",
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

Project support:

* source code hosted at `github.com`_.
* distributed through `PyPI`_.
* documentation hosted at `readthedocs.org`_.

|pypi_version| |build_status| |coverage|

[kwyjii@gmail.com]



.. _github.com: https://github.com/joeyjojojrshabadu/httpclienttest
.. _PyPI: http://pypi.python.org/pypi/
.. _readthedocs.org: 

.. |build_status| image:: https://secure.travis-ci.org/
   :target: https://travis-ci.org/
   :alt: Current build status

.. |coverage| image:: https://coveralls.io/repos/
   :target: https://coveralls.io/r/
   :alt: Latest PyPI version

.. |pypi_version| image:: https://pypip.in/v/
   :target: https://crate.io/packages/
   :alt: Latest PyPI version