from tempfile import TemporaryDirectory
import dependency
import inspect
import os
import unittest


@dependency.provider
def get_temp_dir() -> TemporaryDirectory:
    return TemporaryDirectory()


def test_list_empty_directory(tmp_dir: TemporaryDirectory):
    assert len(os.listdir(tmp_dir.name)) == 0


def test_list_nonempty_directory(tmp_dir: TemporaryDirectory):
    path = os.path.join(tmp_dir.name, 'example.txt')
    open(path, 'w').close()
    assert len(os.listdir(tmp_dir.name)) == 1


if __name__ == "__main__":
    # Gather all the test functions.
    test_functions = [
        func
        for name, func in globals().items()
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
