from numpy import array_equal

PASSED = 0
FAILED = 0

def print_passed(name):
    global PASSED
    print("Test Passed! '{}'".format(name))
    PASSED += 1

def print_failed(name, err):
    global FAILED
    print("\033[1;31;40mTest FAILED! '{}', {}\033[0;37;40m".format(name, err))
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

def assert_all_equal(expected_l, result_l, name):
    for elem in expected_l:
        if not elem in result_l:
            str_list_exp = ", ".join([str(v) for v in expected_l])
            str_list_res = ", ".join([str(v) for v in result_l])
            print_failed(name, "expected [{}], but got [{}]".format(str_list_exp, str_list_res))
            return
    print_passed(name)
