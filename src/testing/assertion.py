PASSED = 0
FAILED = 0

def print_passed(name):
    global PASSED
    print("Test Passed! '{}'".format(name))
    PASSED += 1

def print_failed(name, err):
    global FAILED
    print("Test FAILED! '{}', {}".format(name, err))
    FAILED += 1

def assert_true(val, name):
    if val:
        print_passed(name)
    else:
        print_failed(name, "assert true was false")

def assert_equal(expected, result, name):
    if result == expected:
        print_passed(name)
    else:
        print_failed(name, "expected {}, but got {}".format(expected, result))
