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
class TestProgramFacadeIntegration:
    def setup_method(self, method):
        self.facade = WindowsProgramFacadeCore()
        
        # Load the sample data
        self.samples = program_facade_data
            
    def test_window_listener_with_mocks(self):
        """Test window listener with mocked window changes."""
        with ExitStack() as stack:
            mock_get_window = stack.enter_context(patch('win32gui.GetForegroundWindow'))
            mock_process = stack.enter_context(patch('psutil.Process'))
            mock_get_title = stack.enter_context(patch('win32gui.GetWindowText'))
            mock_get_pid = stack.enter_context(patch('win32process.GetWindowThreadProcessId'))

            # Set up the mock to return different window handles
            mock_window_handles = [1000, 2000, 3000]
            mock_get_window.side_effect = mock_window_handles

            # Set up process mocks
            mock_process_instances = []
            for sample in self.samples[:3]:
                mock_proc = MagicMock()
                mock_proc.name.return_value = sample['process_name']
                mock_proc.exe.return_value = sample.get('exe_path', '')
                mock_process_instances.append(mock_proc)
            mock_process.side_effect = mock_process_instances

            # Set up window title and PID mocks
            mock_get_title.side_effect = [s['window_title'] for s in self.samples[:3]]
            mock_get_pid.side_effect = [(0, s.get('pid', 1000)) for s in self.samples[:3]]

            for s in self.samples:
                print("samples:", s)

            # Run the generator for 3 iterations
            generator = self.facade.listen_for_window_changes()
            results = []
            for i in range(0, 3):
                print(i)
                result = next(generator)
                results.append(result)

            # Verify results match our samples
            for i, result in enumerate(results):
                assert result['process_name'] == self.samples[i]['process_name']
                assert result['window_title'] == self.samples[i]['window_title']
            
            # -- 
            # -- Act: Run the facade
            # -- 
            result1 = self.facade._read_windows()
            result2 = self.facade._read_windows()
            result3 = self.facade._read_windows()
            # --
            # -- Assert
            # --
            def assert_correct_result(result, sample):
                assert result["os"] == "Windows"
                assert result["pid"] == sample["pid"]
                assert result["exe_path"] == sample["exe_path"]
                assert result["process_name"] == sample["process_name"]
            
            assert_correct_result(result1, self.samples[0])
            assert_correct_result(result2, self.samples[1])
            assert_correct_result(result3, self.samples[2])
