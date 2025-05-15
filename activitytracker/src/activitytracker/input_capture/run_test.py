from .test_run_manager import TestRunManager
from .test_schema_manager import test_schema_manager


class TestRunner:
    """
    A large class that runs the whole system using inputs from the test.

    Chrome Ext inputs will be gathered via GET request one at a time.
    """

    def __init__(self, schema_name) -> None:
        self.schema_name = schema_name
        self.passed = 0
        self.failures = 0

    def run_test(self, path_to_inputs):
        pass

    def verify_results(self):
        return self


# When running tests:
def run_test(test_run_manager):
    # 1. Create test schema
    schema_name = test_schema_manager.create_schema(
        test_name="Netflix Viewing Test", input_file="captured_events_2025_05_15.json"
    )

    # 2. Run test against captured inputs
    test_runner = TestRunner(schema_name)
    result = test_runner.run_test("captured_events_2025_05_15.json")

    # 3. Verify results
    verification = test_runner.verify_results()

    # 4. Record test outcome
    test_run_manager.record_event(
        "TEST_COMPLETED",
        {
            "passed": verification.passed,
            "failures": verification.failures,
            "input_file": "captured_events_2025_05_15.json",
        },
    )
