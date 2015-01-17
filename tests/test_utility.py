import unittest
import requests
from httpclienttest.httpserver import LIST, CLEAR, GETROUTE, LAST
from httpclienttest import HttpTests, add_route, delete_route, start_http


class TestUtilityFunctions(unittest.TestCase):

    """
    Test the utility functions exposed by the tests server
    """

    def setUp(self):
        self.ht = HttpTests()
        self.test1 = '/test'
        self.test2 = '/blah'
        self.test3 = '/route/<param>'
        self.req1, _ = self.ht.add_route('/test')
        self.req2, _ = self.ht.add_route('/blah')
        self.req3, _ = self.ht.add_route(self.test3, 'POST')

    def test_get_last_call(self):
        """
        Test that we retrieve only the last call made
        """
        last_func = getattr(self.ht, LAST)
        requests.get(self.req1)
        last_call = last_func()
        self.assertIn(self.test1, last_call['urlparts'],
                         "Incorrect last call")

        requests.get(self.req2)
        last_call = last_func()
        self.assertIn(self.test2, last_call['urlparts'],
                         "Incorrect last call")

    def test_get_last_request(self):
        """
        Test that we can retreive the last call to a specific route
        """
        req_func = getattr(self.ht, GETROUTE)
        requests.get(self.req2)
        requests.get(self.req2)
        requests.post(self.ht.base + '/route/12345')

        res = req_func(self.test1, 'GET')
        self.assertIn(self.test1, res['urlparts'],
                         "Incorrect last call")
        self.assertEqual(res['method'], 'GET', "Incorrect method")

        res = req_func(self.test2, 'GET')
        self.assertIn(self.test2, res['urlparts'],
                         "Incorrect last call")
        self.assertEqual(res['method'], 'GET', "Incorrect method")

        res = req_func(self.test3, 'POST')
        self.assertIn('/route/12345', res['urlparts'],
                         "Incorrect last call")
        self.assertEqual(res['method'], 'POST', "Incorrect method")

    def test_get_last_request_contents(self):
        """
        Test that the contents of the response are expected
        """
        req_func = getattr(self.ht, GETROUTE)
        requests.post(self.ht.base + '/route/12345?key=val', 'postdata')

        res = req_func(self.test3, 'POST')
        self.assertEqual(res['query_string'], 'key=val',
                         'query_string incorrect')
        self.assertEqual(res['method'], 'POST', 'method incorrect')
        #self.assertEqual(res['body'], 'postdata')
        self.assertDictEqual(res['query_params'], {'key': 'val'},
                             'query_params does not contain expected dict')
        self.assertDictEqual(res['args'], {'param': '12345'},
                             'args does not contain expected dict')

        for header in ['Content-Length', 'User-Agent', 'Content-Type']:
            self.assertIn(header, res['headers'].keys(),
                          '%s should be in headers % header')

    def test_get_all_calls(self):
        """
        Test that a list of all calls made to server are retreived
        """
        list_func = getattr(self.ht, LIST)

        requests.get(self.req1)
        requests.get(self.req2)
        requests.post(self.ht.base + '/route/12345')

        res = list_func()
        req_list = [self.test1, self.test2, self.test3]
        self.assertEqual(res.keys(), req_list, 'expected 3 routes')

    def test_clear_list(self):
        """
        Test that the list of all calls can be cleared
        """
        clear_func = getattr(self.ht, CLEAR)
        list_func = getattr(self.ht, LIST)

        requests.get(self.req1)
        requests.get(self.req2)
        requests.post(self.ht.base + '/route/12345')

        clear_func()
        self.assertEqual(len(list_func()), 0, 'call dict should be empty')

    test = '/test'

    class TestAsserts(unittest.TestCase):

        """
        Test assertions
        """
        @add_route('/test')
        def test_assert_route_called(self):
            """
            Test route is called
            """
            requests.get(self.ht.base + test)
            self.assertRouteCalled(test, 'GET')

        @add_route('/test')
        def test_assert_count_route_called(self):
            """
            Test route called count
            """
            for i in range(3):
                requests.get(self.ht.base + test)

            self.assertCountRouteCalled(test, 3)

        @add_route('/test/<arg1>/<arg2>')
        def test_assert_arguments(self):
            """
            Test the argument assertion
            """
            requests.get(self.ht.base + '/test/1234/5678')
            arg_dict = {'arg1': '1234', 'arg2': '5678'}

            self.assertLastRouteCallArguments('/test/<arg1>/<arg2>', arg_dict,
                                              err_msg='incorrect args')

        @add_route('/test')
        def test_assert_params(self):
            """
            Test the arguments assertion
            """
            requests.get(self.ht.base + test + '?p1=1234&p2=5678')
            param_dict = {'p1': '1234', 'p2': '5678'}

            self.assertLastRouteCallParams(test, param_dict)
