httpclienttest - HTTP Client testing library
********************************

httpclienttest simplifies unit testing of HTTP clients written in Python.

httpclienttest allows for one line creation of a dummy Bottle server with
configurable routes and utility functionality to easily test that requests
are being generated correctly, and responses are being parsed as expected.

httpclienttest can be used in one of two ways:

- By obtaining the singleton HttpTests object
to define a dummy server and provide assertions for test

- By decorating test functions to add routes

Example code can be found in example.py and dec_example.py

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