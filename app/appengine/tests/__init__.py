# -*- coding: utf-8 -*-
"""
    To run the tests:

    1. Install nose and nosegae

    2. Run nosetests in the tests dir. Optionally you can define a temporary
       directory for the datastore used in the tests.

       $ nosetests --with-gae --gae-datastore=/path/to/test/datastore
"""
import sys
from os import path

gaefy_path = path.abspath(path.join(path.dirname(__file__), '..'))
sys.path.insert(0, gaefy_path)
