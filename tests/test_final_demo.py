import importlib
import inspect


TEST_MODULES = [
    "tests.test_protected_tools",
    "tests.test_agent_injection",
    "tests.test_injection_block",
    "tests.test_approval_security",
    "tests.test_approval_rejection",
    "tests.test_unknown_tool",
    "tests.test_malformed_arguments",
    "tests.test_missing_arguments",
    "tests.test_approval_tampering",
    "tests.test_audit_logging",
    "tests.test_audit_tampering",
    "tests.test_audit_chain",
    "tests.test_approval_authorization",
    "tests.test_approval_identity_tampering",
]


def find_test_functions(module):
    functions = []

    for name, function in inspect.getmembers(
        module,
        inspect.isfunction,
    ):
        if name.startswith("test_"):
            functions.append((name, function))

    return functions


def main():
    print()
    print("=" * 70)
    print("AURELIA INSURANCE SECURITY GATEWAY")
    print("FINAL SECURITY DEMONSTRATION")
    print("=" * 70)

    total = 0
    passed = 0
    failed = 0

    for module_name in TEST_MODULES:
        print()
        print("-" * 70)
        print(f"MODULE: {module_name}")
        print("-" * 70)

        module = importlib.import_module(module_name)

        test_functions = find_test_functions(module)

        if not test_functions:
            print("No test functions found.")
            continue

        for test_name, test_function in test_functions:
            total += 1

            print()
            print(f"RUNNING: {test_name}")
            print("-" * 70)

            try:
                test_function()

                passed += 1

                print()
                print(f"PASSED: {test_name}")

            except Exception as error:
                failed += 1

                print()
                print(f"FAILED: {test_name}")
                print(f"ERROR: {error}")

    print()
    print("=" * 70)
    print("FINAL SECURITY DEMONSTRATION COMPLETE")
    print("=" * 70)

    print()
    print(f"TOTAL TESTS:  {total}")
    print(f"PASSED:       {passed}")
    print(f"FAILED:       {failed}")

    print()

    if failed == 0:
        print("SECURITY GATEWAY STATUS: PASS")
        print()
        print("PROJECT SECURITY VALIDATION PASSED")
    else:
        print("SECURITY GATEWAY STATUS: FAIL")
        print()
        print("PROJECT SECURITY VALIDATION FAILED")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
