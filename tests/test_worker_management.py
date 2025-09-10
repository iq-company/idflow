#!/usr/bin/env python3
"""
Unit tests for worker management functionality.

Tests the worker ps and killall commands with proper filtering
and output formatting.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import os
import signal
from pathlib import Path

from idflow.cli.worker.worker import list_running_workers, kill_workers


class TestWorkerProcessListing:
    """Test the worker process listing functionality."""

    def test_ps_filters_worker_processes(self):
        """Test that ps command filters for actual worker processes."""
        # Mock ps aux output
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  12345  6789 ?        Ss   10:00   0:01 /sbin/init
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
usr       1235  0.1  0.2  23457  7891 pts/1    S+   10:01   0:00 python -m idflow worker start --worker stage_evaluation
usr       1236  0.0  0.1  12346  6788 ?        S    10:01   0:00 kworker/0:0
root      1237  0.0  0.1  12347  6787 ?        S    10:01   0:00 kworker/0:1
usr       1238  0.1  0.2  23458  7892 pts/2    S+   10:01   0:00 idflow worker ps
usr       1239  0.1  0.2  23459  7893 pts/3    S+   10:01   0:00 idflow worker killall
usr       1240  0.1  0.2  23460  7894 pts/4    S+   10:01   0:00 python -m idflow worker start --all
usr       1241  0.1  0.2  23461  7895 pts/5    S+   10:01   0:00 python -m conductor worker start
usr       1242  0.1  0.2  23462  7896 pts/6    S+   10:01   0:00 python -m idflow worker list
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            # Mock typer.echo to capture output
            with patch('typer.echo') as mock_echo:
                list_running_workers()

                # Should only show actual worker processes
                echo_calls = mock_echo.call_args_list

                # Should show header
                assert any("WORKER" in str(call) for call in echo_calls)

                # Should show worker processes (not ps, killall, list commands)
                worker_lines = [call for call in echo_calls if "update_stage_status" in str(call) or "stage_evaluation" in str(call) or "--all" in str(call)]
                assert len(worker_lines) == 3  # 3 actual workers

    def test_ps_extracts_worker_names(self):
        """Test that ps command extracts worker names correctly."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
usr       1235  0.1  0.2  23457  7891 pts/1    S+   10:01   0:00 python -m idflow worker start --worker stage_evaluation
usr       1240  0.1  0.2  23460  7894 pts/4    S+   10:01   0:00 python -m idflow worker start --all
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                list_running_workers()

                # Check that worker names are extracted and displayed
                echo_calls = mock_echo.call_args_list
                worker_lines = [call for call in echo_calls if "update_stage_status" in str(call) or "stage_evaluation" in str(call) or "all" in str(call)]

                # Should show worker names in first column
                assert any("update_stage_status" in str(call) for call in worker_lines)
                assert any("stage_evaluation" in str(call) for call in worker_lines)
                assert any("all" in str(call) for call in worker_lines)

    def test_ps_full_command_option(self):
        """Test that --full option shows complete command."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                list_running_workers(full_command=True)

                # Should show full command in output
                echo_calls = mock_echo.call_args_list
                assert any("python -m idflow worker start --worker update_stage_status" in str(call) for call in echo_calls)

    def test_ps_no_workers_found(self):
        """Test that ps command handles no workers found."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  12345  6789 ?        Ss   10:00   0:01 /sbin/init
usr       1238  0.1  0.2  23458  7892 pts/2    S+   10:01   0:00 idflow worker ps
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                list_running_workers()

                # Should show no workers message
                echo_calls = mock_echo.call_args_list
                assert any("No worker processes found" in str(call) for call in echo_calls)


class TestWorkerKilling:
    """Test the worker killing functionality."""

    def test_killall_finds_matching_workers(self):
        """Test that killall finds workers matching pattern."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
usr       1235  0.1  0.2  23457  7891 pts/1    S+   10:01   0:00 python -m idflow worker start --worker stage_evaluation
usr       1240  0.1  0.2  23460  7894 pts/4    S+   10:01   0:00 python -m idflow worker start --all
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern="update_stage_status")

                # Should find and kill matching worker
                echo_calls = mock_echo.call_args_list
                assert any("Found 1 worker processes matching pattern 'update_stage_status'" in str(call) for call in echo_calls)
                import signal
                # The test uses kill=True by default, so it should be SIGKILL
                mock_kill.assert_called_once_with(1234, signal.SIGKILL)

    def test_killall_kills_all_workers_without_pattern(self):
        """Test that killall kills all workers when no pattern specified."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
usr       1235  0.1  0.2  23457  7891 pts/1    S+   10:01   0:00 python -m idflow worker start --worker stage_evaluation
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern=None)

                # Should find and kill all workers
                echo_calls = mock_echo.call_args_list
                assert any("Found 2 worker processes matching all workers" in str(call) for call in echo_calls)
                assert mock_kill.call_count == 2

    def test_killall_uses_sigkill_with_kill_option(self):
        """Test that killall uses SIGKILL with --kill option."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern="update_stage_status", kill=True)

                # Should use SIGKILL
                mock_kill.assert_called_once_with(1234, signal.SIGKILL)

    def test_killall_skips_confirmation_with_yes_option(self):
        """Test that killall skips confirmation with --yes option."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                kill_workers(pattern="update_stage_status", yes=True)

                # Should not call confirm
                mock_confirm.assert_not_called()
                # Should still kill the process
                mock_kill.assert_called_once()

    def test_killall_handles_kill_errors(self):
        """Test that killall handles kill errors gracefully."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True
                mock_kill.side_effect = ProcessLookupError("Process not found")

                kill_workers(pattern="update_stage_status")

                # Should handle error gracefully
                echo_calls = mock_echo.call_args_list
                assert any("already terminated" in str(call) for call in echo_calls)

    def test_killall_handles_permission_errors(self):
        """Test that killall handles permission errors gracefully."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True
                mock_kill.side_effect = PermissionError("Permission denied")

                kill_workers(pattern="update_stage_status")

                # Should handle error gracefully
                echo_calls = mock_echo.call_args_list
                assert any("Permission denied" in str(call) for call in echo_calls)

    def test_killall_substring_matching(self):
        """Test that killall uses substring matching for patterns."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
usr       1235  0.1  0.2  23457  7891 pts/1    S+   10:01   0:00 python -m idflow worker start --worker stage_evaluation
usr       1240  0.1  0.2  23460  7894 pts/4    S+   10:01   0:00 python -m idflow worker start --worker other_worker
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern="stage")

                # Should find both stage-related workers
                echo_calls = mock_echo.call_args_list
                assert any("Found 2 worker processes matching pattern 'stage'" in str(call) for call in echo_calls)
                assert mock_kill.call_count == 2

    def test_killall_case_insensitive_matching(self):
        """Test that killall uses case-insensitive matching."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker UPDATE_STAGE_STATUS
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern="update_stage_status")

                # Should find worker despite case difference
                echo_calls = mock_echo.call_args_list
                assert any("Found 1 worker processes matching pattern 'update_stage_status'" in str(call) for call in echo_calls)
                mock_kill.assert_called_once()

    def test_killall_no_matching_workers(self):
        """Test that killall handles no matching workers."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker other_worker
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                kill_workers(pattern="update_stage_status")

                # Should show no matching workers message
                echo_calls = mock_echo.call_args_list
                assert any("No worker processes found matching pattern 'update_stage_status'" in str(call) for call in echo_calls)


class TestWorkerOutputFormatting:
    """Test worker command output formatting."""

    def test_ps_table_formatting(self):
        """Test that ps command formats output as a table."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                list_running_workers()

                # Should show table header
                echo_calls = mock_echo.call_args_list
                assert any("WORKER" in str(call) and "USER" in str(call) and "PID" in str(call) for call in echo_calls)

    def test_killall_table_formatting(self):
        """Test that killall command formats output as a table."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                kill_workers(pattern="update_stage_status")

                # Should show table header
                echo_calls = mock_echo.call_args_list
                assert any("WORKER" in str(call) and "USER" in str(call) and "PID" in str(call) for call in echo_calls)

    def test_killall_shows_signal_used(self):
        """Test that killall shows which signal was used."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
usr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                # Test SIGTERM
                kill_workers(pattern="update_stage_status", kill=False)

                echo_calls = mock_echo.call_args_list
                assert any("SIGTERM" in str(call) for call in echo_calls)

                # Reset mock
                mock_echo.reset_mock()
                mock_kill.reset_mock()

                # Test SIGKILL
                kill_workers(pattern="update_stage_status", kill=True)

                echo_calls = mock_echo.call_args_list
                assert any("SIGKILL" in str(call) for call in echo_calls)


class TestWorkerSignalHandling:
    """Test the worker signal handling functionality."""

    def test_signal_handler_stops_workers_cleanly(self):
        """Test that signal handler stops workers cleanly on SIGINT."""
        from idflow.cli.worker.worker import start_workers
        from unittest.mock import patch, MagicMock

        # Mock the TaskHandler
        mock_task_handler = MagicMock()

        # Mock worker files to ensure we have workers to start
        mock_worker_files = [Path("test_worker.py")]

        with patch('idflow.cli.worker.worker.TaskHandler', return_value=mock_task_handler), \
             patch('idflow.cli.worker.worker.discover_worker_files', return_value=mock_worker_files), \
             patch('idflow.cli.worker.worker.extract_task_name_from_file', return_value="test_worker"), \
             patch('idflow.cli.worker.worker.load_task_function'), \
             patch('typer.echo') as mock_echo, \
             patch('signal.signal') as mock_signal, \
             patch('time.sleep', side_effect=KeyboardInterrupt()):

            # This should not raise an exception
            try:
                start_workers(all=True)
            except (SystemExit, KeyboardInterrupt):
                pass  # Expected to exit

            # Verify signal handlers were set up
            assert mock_signal.call_count == 2  # SIGINT and SIGTERM

            # Verify task handler was created
            mock_task_handler.start_processes.assert_called_once()

    def test_signal_handler_handles_double_interrupt(self):
        """Test that signal handler handles double interrupt gracefully."""
        from idflow.cli.worker.worker import start_workers
        from unittest.mock import patch, MagicMock

        # Mock the TaskHandler
        mock_task_handler = MagicMock()

        # Mock worker files to ensure we have workers to start
        mock_worker_files = [Path("test_worker.py")]

        with patch('idflow.cli.worker.worker.TaskHandler', return_value=mock_task_handler), \
             patch('idflow.cli.worker.worker.discover_worker_files', return_value=mock_worker_files), \
             patch('idflow.cli.worker.worker.extract_task_name_from_file', return_value="test_worker"), \
             patch('idflow.cli.worker.worker.load_task_function'), \
             patch('typer.echo') as mock_echo, \
             patch('signal.signal') as mock_signal, \
             patch('sys.exit') as mock_exit:

            # Simulate double interrupt
            def simulate_double_interrupt():
                # First interrupt
                signal_handler = mock_signal.call_args_list[0][0][1]
                signal_handler(signal.SIGINT, None)
                # Second interrupt (should force exit)
                signal_handler(signal.SIGINT, None)

            with patch('time.sleep', side_effect=simulate_double_interrupt):
                try:
                    start_workers(all=True)
                except (SystemExit, KeyboardInterrupt):
                    pass  # Expected to exit

            # Verify both interrupts were handled
            assert mock_exit.call_count >= 1

    def test_signal_handler_handles_stop_errors(self):
        """Test that signal handler handles errors during worker stop."""
        from idflow.cli.worker.worker import start_workers
        from unittest.mock import patch, MagicMock

        # Mock the TaskHandler to raise an error during stop
        mock_task_handler = MagicMock()
        mock_task_handler.stop_processes.side_effect = Exception("Stop error")

        # Mock worker files to ensure we have workers to start
        mock_worker_files = [Path("test_worker.py")]

        with patch('idflow.cli.worker.worker.TaskHandler', return_value=mock_task_handler), \
             patch('idflow.cli.worker.worker.discover_worker_files', return_value=mock_worker_files), \
             patch('idflow.cli.worker.worker.extract_task_name_from_file', return_value="test_worker"), \
             patch('idflow.cli.worker.worker.load_task_function'), \
             patch('typer.echo') as mock_echo, \
             patch('signal.signal') as mock_signal, \
             patch('sys.exit') as mock_exit:

            # Simulate interrupt by calling the signal handler directly
            def simulate_interrupt():
                # Get the signal handler from the first call
                signal_handler = mock_signal.call_args_list[0][0][1]
                signal_handler(signal.SIGINT, None)

            with patch('time.sleep', side_effect=simulate_interrupt):
                try:
                    start_workers(all=True)
                except (SystemExit, KeyboardInterrupt):
                    pass  # Expected to exit

            # Verify error was handled gracefully
            echo_calls = mock_echo.call_args_list
            # Check if any echo call contains error messages
            error_found = any("Error during shutdown" in str(call) for call in echo_calls)
            workers_stopped_found = any("Workers stopped" in str(call) for call in echo_calls)
            error_starting_found = any("Error starting workers" in str(call) for call in echo_calls)
            error_cleanup_found = any("Error during cleanup" in str(call) for call in echo_calls)

            # At least one of these should be true
            assert error_found or workers_stopped_found or error_starting_found or error_cleanup_found, f"Expected error handling messages, got: {[str(call) for call in echo_calls]}"
