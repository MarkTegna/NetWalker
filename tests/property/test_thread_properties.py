"""
Property-based tests for ThreadManager

Tests universal properties of concurrent processing functionality.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import time
import threading
from unittest.mock import Mock
from concurrent.futures import Future

from netwalker.discovery.thread_manager import ThreadManager, ThreadTask, ThreadResult, ThreadSafeCounter


class TestThreadManagerProperties:
    """Property-based tests for ThreadManager functionality"""
    
    def create_test_config(self, max_connections: int = 5) -> dict:
        """Create test configuration"""
        return {
            'max_concurrent_connections': max_connections,
            'connection_timeout_seconds': 5,
            'task_timeout_seconds': 10
        }
    
    def create_test_task(self, hostname: str, ip_address: str, 
                        should_succeed: bool = True, delay: float = 0.1) -> ThreadTask:
        """Create a test task"""
        def test_function(*args, **kwargs):
            time.sleep(delay)
            if should_succeed:
                return f"Success for {hostname}:{ip_address}"
            else:
                raise Exception(f"Test failure for {hostname}:{ip_address}")
        
        return ThreadTask(
            task_id=f"{hostname}:{ip_address}",
            hostname=hostname,
            ip_address=ip_address,
            task_function=test_function,
            task_args=(),
            task_kwargs={}
        )
    
    @given(
        max_connections=st.integers(min_value=1, max_value=5),
        num_tasks=st.integers(min_value=1, max_value=10)
    )
    @settings(deadline=2000)  # 2 second deadline for threading tests
    def test_connection_limit_enforcement_property(self, max_connections, num_tasks):
        """
        Property 27: Connection Limit Enforcement
        
        The number of concurrent connections should never exceed the configured limit.
        """
        assume(num_tasks >= max_connections)  # Need enough tasks to test the limit
        
        config = self.create_test_config(max_connections)
        thread_manager = ThreadManager(config)
        
        max_concurrent_observed = 0
        concurrent_counter = ThreadSafeCounter(0)
        
        def tracking_task():
            """Task that tracks concurrent execution"""
            current = concurrent_counter.increment()
            nonlocal max_concurrent_observed
            max_concurrent_observed = max(max_concurrent_observed, current)
            
            time.sleep(0.05)  # Reduced sleep time
            
            concurrent_counter.decrement()
            return "completed"
        
        try:
            thread_manager.start()
            
            # Submit tasks
            tasks = []
            for i in range(num_tasks):
                task = ThreadTask(
                    task_id=f"task_{i}",
                    hostname=f"host_{i}",
                    ip_address=f"192.168.1.{i % 255}",
                    task_function=tracking_task,
                    task_args=(),
                    task_kwargs={}
                )
                tasks.append(task)
                thread_manager.submit_task(task)
            
            # Wait for completion
            thread_manager.wait_for_completion(timeout=10)
            
            # Property: Max concurrent should not exceed limit
            assert max_concurrent_observed <= max_connections, \
                f"Observed {max_concurrent_observed} concurrent, limit was {max_connections}"
            
        finally:
            thread_manager.stop()
    
    @given(
        tasks=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
                st.ip_addresses(v=4).map(str),
                st.booleans()  # success/failure
            ),
            min_size=1, max_size=5,
            unique_by=lambda x: f"{x[0]}:{x[1]}"
        )
    )
    @settings(deadline=2000)  # 2 second deadline
    def test_thread_safety_maintenance_property(self, tasks):
        """
        Property 28: Thread Safety Maintenance
        
        Shared data structures should remain consistent under concurrent access.
        """
        config = self.create_test_config(5)
        thread_manager = ThreadManager(config)
        
        try:
            thread_manager.start()
            
            # Submit all tasks
            submitted_tasks = []
            for hostname, ip_address, should_succeed in tasks:
                task = self.create_test_task(hostname, ip_address, should_succeed, 0.02)  # Reduced delay
                submitted_tasks.append(task)
                success = thread_manager.submit_task(task)
                assert success, f"Failed to submit task {task.task_id}"
            
            # Wait for completion
            completed = thread_manager.wait_for_completion(timeout=10)
            assert completed, "Tasks did not complete within timeout"
            
            # Get all results
            results = thread_manager.get_results()
            
            # Property: Number of results should match number of submitted tasks
            assert len(results) == len(submitted_tasks), \
                f"Expected {len(submitted_tasks)} results, got {len(results)}"
            
            # Property: Each task should have exactly one result
            result_task_ids = {result.task_id for result in results}
            submitted_task_ids = {task.task_id for task in submitted_tasks}
            assert result_task_ids == submitted_task_ids, \
                "Result task IDs don't match submitted task IDs"
            
            # Property: Statistics should be consistent
            stats = thread_manager.get_statistics()
            assert stats['tasks_submitted'] == len(submitted_tasks)
            assert stats['tasks_completed'] + stats['tasks_failed'] == len(submitted_tasks)
            
        finally:
            thread_manager.stop()
    
    @given(
        successful_tasks=st.integers(min_value=1, max_value=3),
        failing_tasks=st.integers(min_value=1, max_value=3)
    )
    @settings(deadline=2000)  # 2 second deadline
    def test_error_isolation_property(self, successful_tasks, failing_tasks):
        """
        Property: Failed tasks should not affect successful tasks
        """
        config = self.create_test_config(10)
        thread_manager = ThreadManager(config)
        
        try:
            thread_manager.start()
            
            all_tasks = []
            
            # Add successful tasks
            for i in range(successful_tasks):
                task = self.create_test_task(f"success_{i}", f"192.168.1.{i}", True, 0.02)
                all_tasks.append((task, True))
                thread_manager.submit_task(task)
            
            # Add failing tasks
            for i in range(failing_tasks):
                task = self.create_test_task(f"fail_{i}", f"192.168.2.{i}", False, 0.02)
                all_tasks.append((task, False))
                thread_manager.submit_task(task)
            
            # Wait for completion
            completed = thread_manager.wait_for_completion(timeout=10)
            assert completed, "Tasks did not complete within timeout"
            
            # Get results
            results = thread_manager.get_results()
            
            # Property: All tasks should have results
            assert len(results) == len(all_tasks)
            
            # Property: Successful tasks should succeed, failing tasks should fail
            success_count = sum(1 for result in results if result.success)
            failure_count = sum(1 for result in results if not result.success)
            
            assert success_count == successful_tasks, \
                f"Expected {successful_tasks} successes, got {success_count}"
            assert failure_count == failing_tasks, \
                f"Expected {failing_tasks} failures, got {failure_count}"
            
        finally:
            thread_manager.stop()
    
    def test_context_manager_property(self):
        """
        Property: ThreadManager should work as a context manager
        """
        config = self.create_test_config(3)
        
        with ThreadManager(config) as thread_manager:
            # Should be started automatically
            assert thread_manager.executor is not None
            
            # Submit a simple task
            task = self.create_test_task("test", "192.168.1.1", True, 0.02)
            success = thread_manager.submit_task(task)
            assert success
            
            # Wait for completion
            completed = thread_manager.wait_for_completion(timeout=5)
            assert completed
        
        # Should be stopped automatically
        # Note: executor might be None after shutdown


class TestThreadSafeCounterProperties:
    """Property-based tests for ThreadSafeCounter"""
    
    @given(
        initial_value=st.integers(min_value=0, max_value=100),
        increments=st.integers(min_value=0, max_value=50),
        decrements=st.integers(min_value=0, max_value=50)
    )
    def test_counter_consistency_property(self, initial_value, increments, decrements):
        """
        Property: Counter operations should be consistent and thread-safe
        """
        counter = ThreadSafeCounter(initial_value)
        
        # Perform increments
        for _ in range(increments):
            counter.increment()
        
        # Perform decrements
        for _ in range(decrements):
            counter.decrement()
        
        # Property: Final value should be initial + increments - decrements
        expected_value = initial_value + increments - decrements
        assert counter.get_value() == expected_value
    
    def test_concurrent_counter_operations_property(self):
        """
        Property: Counter should maintain consistency under concurrent access
        """
        counter = ThreadSafeCounter(0)
        num_threads = 10
        operations_per_thread = 100
        
        def increment_worker():
            for _ in range(operations_per_thread):
                counter.increment()
        
        def decrement_worker():
            for _ in range(operations_per_thread):
                counter.decrement()
        
        # Start threads
        threads = []
        
        # Half increment, half decrement
        for i in range(num_threads):
            if i % 2 == 0:
                thread = threading.Thread(target=increment_worker)
            else:
                thread = threading.Thread(target=decrement_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Property: Final value should be predictable
        # Half threads increment, half decrement
        increment_threads = (num_threads + 1) // 2
        decrement_threads = num_threads // 2
        
        expected_value = (increment_threads * operations_per_thread) - (decrement_threads * operations_per_thread)
        assert counter.get_value() == expected_value


class TestThreadTaskProperties:
    """Property-based tests for ThreadTask"""
    
    @given(
        hostname=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        ip_address=st.ip_addresses(v=4).map(str),
        priority=st.integers(min_value=0, max_value=10)
    )
    def test_task_id_generation_property(self, hostname, ip_address, priority):
        """
        Property: Task ID should be generated consistently
        """
        def dummy_function():
            pass
        
        task = ThreadTask(
            task_id="",  # Empty task_id should be auto-generated
            hostname=hostname,
            ip_address=ip_address,
            task_function=dummy_function,
            task_args=(),
            task_kwargs={},
            priority=priority
        )
        
        # Property: Task ID should be hostname:ip_address when not provided
        expected_task_id = f"{hostname}:{ip_address}"
        assert task.task_id == expected_task_id
    
    @given(
        custom_task_id=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
        hostname=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        ip_address=st.ip_addresses(v=4).map(str)
    )
    def test_custom_task_id_property(self, custom_task_id, hostname, ip_address):
        """
        Property: Custom task ID should be preserved
        """
        def dummy_function():
            pass
        
        task = ThreadTask(
            task_id=custom_task_id,
            hostname=hostname,
            ip_address=ip_address,
            task_function=dummy_function,
            task_args=(),
            task_kwargs={}
        )
        
        # Property: Custom task ID should be preserved
        assert task.task_id == custom_task_id