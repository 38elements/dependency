# pip install dependency
import dependency
import inspect
import unittest


def run_tests():
    # Get the global namespace of whichever frame is calling into this function.
    frame = inspect.stack()[1][0]
    objects = frame.f_globals.items()

    # Gather all the test functions.
    test_functions = [
        func
        for name, func in objects
        if name.startswith('test_') and callable(func)
    ]

    # Inject dependencies into test functions.
    injected_functions = [
        dependency.inject(func)
        for func in test_functions
    ]

    # Create and run the complete test suite.
    test_suite = unittest.TestSuite([
        unittest.FunctionTestCase(func)
        for func in injected_functions
    ])
    unittest.TextTestRunner().run(test_suite)


# Example:
#
# from tempfile import TemporaryDirectory
# from test_framework import run_tests
# import dependency
# import os
#
#
# @dependency.provider
# def get_temp_dir() -> TemporaryDirectory:
#     """
#     A temporary directory component that may be injected into test cases.
#     Each directory will only exist for the lifetime of a single test.
#     """
#     return TemporaryDirectory()
#
#
# def test_list_empty_directory(tmp_dir: TemporaryDirectory):
#     assert len(os.listdir(tmp_dir.name)) == 0
#
#
# def test_list_nonempty_directory(tmp_dir: TemporaryDirectory):
#     path = os.path.join(tmp_dir.name, 'example.txt')
#     open(path, 'w').close()
#     assert len(os.listdir(tmp_dir.name)) == 1
#
#
# if __name__ == "__main__":
#     run_tests()
