import unittest
import doctest
import sys
import os
sys.path.append(os.path.abspath("src"))

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocFileSuite("../README.md"))
    return tests
