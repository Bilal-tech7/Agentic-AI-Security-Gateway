"""
Aurelia - Final Security Regression Runner
==========================================

Automatically discovers and runs the complete Aurelia
security test suite.

Core tests are always executed.

Ollama-dependent tests are executed when the local
Ollama service is reachable.

Usage:
    python run_all_tests.py
"""

from pathlib import Path
import subprocess
import sys
import time


# ============================================================
# CONFIGURATION
# ============================================================

TEST_DIRECTORY = Path("tests")

# These tests require a running local Ollama service.
OLLAMA_TEST_FILES = {
    "test_ollama.py",
    "test_agent_gateway.py",
    "test_agent_injection.py",
}


# ============================================================
# TEST DISCOVERY
# ============================================================

def discover_tests():
    """
    Discover all test_*.py files in the tests directory.

    Returns:
        core_tests
        ollama_tests
    """

    if not TEST_DIRECTORY.exists():
        raise RuntimeError(
            "The tests directory does not exist."
        )

    discovered = sorted(
        TEST_DIRECTORY.glob("test_*.py")
    )

    core_tests = []
    ollama_tests = []

    for path in discovered:

        module = (
            str(path.with_suffix(""))
            .replace("\\", ".")
            .replace("/", ".")
        )

        test = {
            "name": path.stem,
            "module": module,
        }

        if path.name in OLLAMA_TEST_FILES:
            ollama_tests.append(test)
        else:
            core_tests.append(test)

    return core_tests, ollama_tests


# ============================================================
# TEST EXECUTION
# ============================================================

def run_test(name, module):
    """
    Run one test module in an isolated Python process.

    Returns:
        True  -> passed
        False -> failed
    """

    print()
    print("=" * 72)
    print(f"RUNNING: {name}")
    print(f"MODULE:  {module}")
    print("=" * 72)

    start = time.time()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            module,
        ],
        check=False,
    )

    elapsed = time.time() - start

    if result.returncode == 0:

        print()
        print(
            f"[PASS] {name} "
            f"({elapsed:.2f}s)"
        )

        return True

    print()
    print(
        f"[FAIL] {name} "
        f"({elapsed:.2f}s)"
    )

    return False


# ============================================================
# OLLAMA CHECK
# ============================================================

def check_ollama():
    """
    Check whether the local Ollama service is reachable.
    """

    try:

        result = subprocess.run(
            [
                "ollama",
                "list",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )

        return result.returncode == 0

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ):

        return False


# ============================================================
# RESULT STORAGE
# ============================================================

def add_result(
    results,
    name,
    status,
):
    results.append(
        {
            "name": name,
            "status": status,
        }
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results):

    print()
    print()
    print("=" * 72)
    print("AURELIA FINAL SECURITY VALIDATION")
    print("=" * 72)

    passed = 0
    failed = 0
    skipped = 0

    for result in results:

        status = result["status"]
        name = result["name"]

        if status == "PASS":

            marker = "[PASS]"
            passed += 1

        elif status == "SKIP":

            marker = "[SKIP]"
            skipped += 1

        else:

            marker = "[FAIL]"
            failed += 1

        print(
            f"{marker:<8} {name}"
        )

    print("-" * 72)

    total = len(results)
    executed = passed + failed

    print(f"Discovered: {total}")
    print(f"Executed:   {executed}")
    print(f"Passed:     {passed}")
    print(f"Failed:     {failed}")
    print(f"Skipped:    {skipped}")

    print("=" * 72)

    if failed == 0:

        print()
        print(
            "FINAL RESULT: "
            "ALL EXECUTED SECURITY TESTS PASSED"
        )

        return True

    print()
    print(
        "FINAL RESULT: "
        "SECURITY REGRESSION FAILED"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 72)
    print("AURELIA")
    print("AGENTIC AI SECURITY GATEWAY")
    print("FINAL REGRESSION SUITE")
    print("=" * 72)

    print()
    print(
        f"Python executable: {sys.executable}"
    )

    # --------------------------------------------------------
    # Discover tests
    # --------------------------------------------------------

    core_tests, ollama_tests = discover_tests()

    print()
    print(
        f"Core tests discovered:   "
        f"{len(core_tests)}"
    )

    print(
        f"Ollama tests discovered: "
        f"{len(ollama_tests)}"
    )

    print(
        f"Total tests discovered:  "
        f"{len(core_tests) + len(ollama_tests)}"
    )

    results = []

    # --------------------------------------------------------
    # Phase 1 - Core tests
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 1 - CORE SECURITY TESTS")
    print("=" * 72)

    for test in core_tests:

        passed = run_test(
            test["name"],
            test["module"],
        )

        add_result(
            results,
            test["name"],
            (
                "PASS"
                if passed
                else "FAIL"
            ),
        )

    # --------------------------------------------------------
    # Phase 2 - Ollama tests
    # --------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 2 - OLLAMA / LLM TESTS")
    print("=" * 72)

    if check_ollama():

        print()
        print(
            "Ollama detected. "
            "Running LLM integration tests."
        )

        for test in ollama_tests:

            passed = run_test(
                test["name"],
                test["module"],
            )

            add_result(
                results,
                test["name"],
                (
                    "PASS"
                    if passed
                    else "FAIL"
                ),
            )

    else:

        print()
        print(
            "Ollama is not currently reachable."
        )

        print(
            "Ollama-dependent tests are being skipped."
        )

        for test in ollama_tests:

            add_result(
                results,
                test["name"],
                "SKIP",
            )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    success = print_summary(
        results
    )

    sys.exit(
        0 if success else 1
    )


if __name__ == "__main__":
    main()