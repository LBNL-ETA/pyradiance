import unittest
import sys

# Import nanobind here. If it fails, we'll assume there's nothing to clean up.
try:
    import nanobind
except ImportError:
    nanobind = None

# Find all files named 'test*.py' in the 'tests' directory.
loader = unittest.TestLoader()
suite = loader.discover('tests')

# Create a TestRunner to execute the tests.
runner = unittest.TextTestRunner(verbosity=2)

# This is the main entry point to run the test suite.
print("--- Running unittest suite ---")
test_result = runner.run(suite)
print("--- Unittest suite finished ---")


# After the test runner has completed, explicitly call nanobind.shutdown()
if nanobind:
    print("\n--- Running nanobind shutdown ---")
    nanobind.shutdown()
    print("--- Nanobind shutdown complete ---")

# This is crucial for CI systems to correctly report failure.
if not test_result.wasSuccessful():
    sys.exit(1)
