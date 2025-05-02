import pytest
from unittest.mock import patch, MagicMock
from unittest.mock import MagicMock
import json
import os
import platform

from contextlib import ExitStack

from ..data.program_facade_data import program_facade_data

if platform.system() != "Windows":
    pytest.skip("Skipping Windows-specific tests on non-Windows platform", allow_module_level=True)


from surveillance.src.facade.program_facade_windows import WindowsProgramFacadeCore


# win32gui.GetForegroundWindow -> gives some truthy value
# win32process.GetWindowThreadProcessId -> gives a PID
# psutil.Process takes an int and gives an obj with an exe() and a name()
# win32gui.GetWindowText(window) -> gives a string

def assert_correct_result(result, sample):
    print(result)
    print(sample, "58ru")
    assert result["os"] == "Windows"
    assert result["pid"] == sample["pid"]
    assert result["exe_path"] == sample["exe_path"]
    assert result["process_name"] == sample["process_name"]
class TestProgramFacadeIntegration:
    def setup_method(self, method):
        self.facade = WindowsProgramFacadeCore()
        
        # Load the sample data
        self.samples = program_facade_data
        # Make them Windows data
        for s in self.samples:
            s["os"] = "Windows"

        mock_process_instances = []
        for sample in self.samples[:3]:
            mock_proc = MagicMock()
            mock_proc.name.return_value = sample['process_name']
            mock_proc.exe.return_value = sample.get('exe_path', '')
            mock_process_instances.append(mock_proc)

        self.mock_process_instances = mock_process_instances
            
    def test_window_listener_with_mocks(self):
        """Test window listener with mocked window changes."""
        with ExitStack() as stack:
            mock_get_window = stack.enter_context(patch('win32gui.GetForegroundWindow'))

            window_handles = [100, 200, 300, 400]  # Different for each iteration
            mock_get_window.side_effect = window_handles

            # Mock the read_windows method to return our sample data instead
            with patch.object(self.facade, '_read_windows') as mock_read:
                mock_read.side_effect = self.samples  # Return samples in sequence
                
                # Run the generator for as many samples as we have
                generator = self.facade.listen_for_window_changes()
                results = []
                
                # Only collect up to the number of samples we have
                for _ in range(min(3, len(self.samples))):
                    try:
                        result = next(generator)
                        results.append(result)
                    except StopIteration:
                        pytest.fail("Generator stopped too early")
                        

                
                # Verify results match our samples
                assert len(results) == min(3, len(self.samples))
                for i, result in enumerate(results):
                    assert_correct_result(self.samples[i], result)

    def test_read_windows(self):
        """Test _read_windows with mocked library responses"""
        with ExitStack() as stack:
            mock_get_window = stack.enter_context(patch('win32gui.GetForegroundWindow'))
            window_handles = [100, 200, 300, 400]  # Different for each iteration
            mock_get_window.side_effect = window_handles

            mock_get_pid = stack.enter_context(patch('win32process.GetWindowThreadProcessId'))
            thread_id_and_pids = [(1, x["pid"]) for x in self.samples]
            mock_get_pid.side_effect = thread_id_and_pids

            # Set up process mocks
            mock_process = stack.enter_context(patch('psutil.Process'))

            mock_process.side_effect = self.mock_process_instances

            mock_get_title = stack.enter_context(patch('win32gui.GetWindowText'))
            window_title_mocks = [s["window_title"] for s in self.samples]
            mock_get_title.side_effect =window_title_mocks


            # Mock the read_windows method to return our sample data instead

            result1 = self.facade._read_windows()
            result2 = self.facade._read_windows()
            result3 = self.facade._read_windows()
            
            assert_correct_result(self.samples[0], result1)
            assert_correct_result(self.samples[1], result2)
            assert_correct_result(self.samples[2], result3)

    def test_two_layers_with_mocks(self):
        """Test listen_for_window_changes with_read_windows having mocked library responses"""
        with ExitStack() as stack:
            mock_get_window = stack.enter_context(patch('win32gui.GetForegroundWindow'))

            # Make sure each pair of consecutive values is different
            # to trigger the window change detection
            irrelevant_start_value = 5
            window_handles = [irrelevant_start_value, 100, 100, 200, 200, 300, 300, 400, 400]  # Duplicated values
            mock_get_window.side_effect = window_handles
            
            # Add time.sleep mock to speed up tests and prevent actual waiting
            stack.enter_context(patch('time.sleep'))

            mock_get_pid = stack.enter_context(patch('win32process.GetWindowThreadProcessId'))
            thread_id_and_pids = [(1, x["pid"]) for x in self.samples]
            mock_get_pid.side_effect = thread_id_and_pids

            # Set up process mocks
            mock_process = stack.enter_context(patch('psutil.Process'))
            mock_process.side_effect = self.mock_process_instances

            mock_get_title = stack.enter_context(patch('win32gui.GetWindowText'))
            window_title_mocks = [s["window_title"] for s in self.samples]
            mock_get_title.side_effect =window_title_mocks


            # Run the generator for as many samples as we have
            generator = self.facade.listen_for_window_changes()
            results = []
            
            # Only collect up to the number of samples we have
            for _ in range(min(3, len(self.samples))):
                try:
                    result = next(generator)
                    print(result, "146ru")
                    results.append(result)
                except StopIteration:
                    pytest.fail("Generator stopped too early")
                
            
            # Verify results match our samples
            assert len(results) == min(3, len(self.samples))
            for i, result in enumerate(results):
                assert_correct_result(self.samples[i], result)

            
            
