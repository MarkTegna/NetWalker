"""
Thread Manager for NetWalker

Provides concurrent processing capabilities for network discovery operations.
Manages connection limits, thread safety, and result synchronization.
"""

import logging
import threading
import time
from typing import Dict, List, Set, Optional, Callable, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass
from queue import Queue, Empty
import traceback

logger = logging.getLogger(__name__)


@dataclass
class ThreadTask:
    """Represents a task to be executed by a thread"""
    task_id: str
    hostname: str
    ip_address: str
    task_function: Callable
    task_args: Tuple
    task_kwargs: Dict[str, Any]
    priority: int = 0  # Higher numbers = higher priority
    
    def __post_init__(self):
        """Ensure task_id is set"""
        if not self.task_id:
            self.task_id = f"{self.hostname}:{self.ip_address}"


@dataclass
class ThreadResult:
    """Result from a thread task execution"""
    task_id: str
    hostname: str
    ip_address: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    thread_id: Optional[str] = None


class ThreadSafeCounter:
    """Thread-safe counter for tracking active connections"""
    
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self) -> int:
        """Increment counter and return new value"""
        with self._lock:
            self._value += 1
            return self._value
    
    def decrement(self) -> int:
        """Decrement counter and return new value"""
        with self._lock:
            self._value -= 1
            return self._value
    
    def get_value(self) -> int:
        """Get current counter value"""
        with self._lock:
            return self._value
    
    def set_value(self, value: int):
        """Set counter value"""
        with self._lock:
            self._value = value


class ThreadManager:
    """
    Manages concurrent processing for network discovery operations.
    
    Features:
    - Connection limit enforcement
    - Thread safety for shared data structures
    - Result synchronization and collection
    - Error isolation for individual threads
    - Priority-based task scheduling
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ThreadManager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Thread configuration
        self.max_concurrent_connections = config.get('max_concurrent_connections', 10)
        self.connection_timeout = config.get('connection_timeout_seconds', 30)
        self.task_timeout = config.get('task_timeout_seconds', 60)
        
        # Thread management
        self.executor: Optional[ThreadPoolExecutor] = None
        self.active_connections = ThreadSafeCounter(0)
        self.connection_semaphore = threading.Semaphore(self.max_concurrent_connections)
        
        # Task and result management
        self.task_queue: Queue[ThreadTask] = Queue()
        self.result_queue: Queue[ThreadResult] = Queue()
        self.active_tasks: Dict[str, Future] = {}
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
        # Thread safety
        self._results_lock = threading.Lock()
        self._tasks_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'max_concurrent_reached': 0,
            'total_execution_time': 0.0
        }
        
        logger.info(f"ThreadManager initialized with max_concurrent_connections={self.max_concurrent_connections}")
    
    def start(self):
        """Start the thread pool executor"""
        if self.executor is None:
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_concurrent_connections,
                thread_name_prefix="NetWalker-Worker"
            )
            logger.info(f"Started ThreadPoolExecutor with {self.max_concurrent_connections} workers")
    
    def stop(self, wait: bool = True, timeout: float = 30.0):
        """
        Stop the thread pool executor.
        
        Args:
            wait: Whether to wait for running tasks to complete
            timeout: Maximum time to wait for tasks to complete (seconds)
        """
        if self.executor is not None:
            logger.info("Shutting down ThreadPoolExecutor")
            
            if wait:
                # First, try to cancel all pending tasks
                logger.info("Cancelling pending tasks...")
                cancelled_count = 0
                with self._tasks_lock:
                    for task_id, future in list(self.active_tasks.items()):
                        if future.cancel():
                            cancelled_count += 1
                            logger.debug(f"Cancelled pending task {task_id}")
                
                if cancelled_count > 0:
                    logger.info(f"Cancelled {cancelled_count} pending tasks")
                
                # Wait for active tasks with timeout
                remaining_tasks = self.get_active_task_count()
                if remaining_tasks > 0:
                    logger.info(f"Waiting up to {timeout} seconds for {remaining_tasks} active tasks to complete...")
                    completed = self.wait_for_completion(timeout=timeout)
                    
                    if not completed:
                        logger.warning(f"Timeout after {timeout} seconds - forcing shutdown")
                        # Force shutdown without waiting
                        self.executor.shutdown(wait=False)
                    else:
                        logger.info("All tasks completed successfully")
                        self.executor.shutdown(wait=True)
                else:
                    logger.info("No active tasks to wait for")
                    self.executor.shutdown(wait=True)
            else:
                # Immediate shutdown
                logger.info("Immediate shutdown requested")
                self.executor.shutdown(wait=False)
            
            self.executor = None
            
            # Reset counters
            self.active_connections.set_value(0)
            
            logger.info("ThreadPoolExecutor shutdown complete")
    
    def submit_task(self, task: ThreadTask) -> bool:
        """
        Submit a task for execution.
        
        Args:
            task: Task to execute
            
        Returns:
            True if task was submitted successfully
        """
        if self.executor is None:
            logger.error("ThreadManager not started - call start() first")
            return False
        
        try:
            # Check if task already exists
            with self._tasks_lock:
                if task.task_id in self.active_tasks or task.task_id in self.completed_tasks:
                    logger.debug(f"Task {task.task_id} already exists, skipping")
                    return False
            
            # Submit task to executor
            future = self.executor.submit(self._execute_task_wrapper, task)
            
            with self._tasks_lock:
                self.active_tasks[task.task_id] = future
            
            with self._stats_lock:
                self._stats['tasks_submitted'] += 1
            
            logger.debug(f"Submitted task {task.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False
    
    def _execute_task_wrapper(self, task: ThreadTask) -> ThreadResult:
        """
        Wrapper for task execution with connection limiting and error handling.
        
        Args:
            task: Task to execute
            
        Returns:
            Thread result
        """
        thread_id = threading.current_thread().name
        start_time = time.time()
        
        # Acquire connection semaphore
        acquired = self.connection_semaphore.acquire(timeout=self.connection_timeout)
        if not acquired:
            error_msg = f"Connection timeout - max concurrent connections ({self.max_concurrent_connections}) reached"
            logger.warning(f"Task {task.task_id}: {error_msg}")
            return ThreadResult(
                task_id=task.task_id,
                hostname=task.hostname,
                ip_address=task.ip_address,
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                thread_id=thread_id
            )
        
        try:
            # Track active connection
            current_connections = self.active_connections.increment()
            
            # Update max concurrent reached
            with self._stats_lock:
                self._stats['max_concurrent_reached'] = max(
                    self._stats['max_concurrent_reached'], 
                    current_connections
                )
            
            logger.debug(f"Task {task.task_id} starting on {thread_id} "
                        f"(active connections: {current_connections})")
            
            # Execute the actual task
            try:
                result = task.task_function(*task.task_args, **task.task_kwargs)
                
                execution_time = time.time() - start_time
                
                thread_result = ThreadResult(
                    task_id=task.task_id,
                    hostname=task.hostname,
                    ip_address=task.ip_address,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    thread_id=thread_id
                )
                
                logger.debug(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Task execution failed: {str(e)}"
                
                logger.error(f"Task {task.task_id} failed: {error_msg}")
                logger.debug(f"Task {task.task_id} traceback: {traceback.format_exc()}")
                
                thread_result = ThreadResult(
                    task_id=task.task_id,
                    hostname=task.hostname,
                    ip_address=task.ip_address,
                    success=False,
                    error=error_msg,
                    execution_time=execution_time,
                    thread_id=thread_id
                )
            
        finally:
            # Always release connection semaphore and decrement counter
            self.connection_semaphore.release()
            self.active_connections.decrement()
        
        # Store result and update tracking
        self._store_result(thread_result)
        
        return thread_result
    
    def _store_result(self, result: ThreadResult):
        """
        Store task result and update tracking.
        
        Args:
            result: Thread result to store
        """
        # Add result to queue
        self.result_queue.put(result)
        
        # Update task tracking
        with self._tasks_lock:
            if result.task_id in self.active_tasks:
                del self.active_tasks[result.task_id]
            
            if result.success:
                self.completed_tasks.add(result.task_id)
            else:
                self.failed_tasks.add(result.task_id)
        
        # Update statistics
        with self._stats_lock:
            if result.success:
                self._stats['tasks_completed'] += 1
            else:
                self._stats['tasks_failed'] += 1
            
            self._stats['total_execution_time'] += result.execution_time
    
    def get_results(self, timeout: Optional[float] = None) -> List[ThreadResult]:
        """
        Get all available results from the result queue.
        
        Args:
            timeout: Maximum time to wait for results
            
        Returns:
            List of thread results
        """
        results = []
        end_time = time.time() + (timeout or 0)
        
        while True:
            try:
                remaining_time = max(0, end_time - time.time()) if timeout else 0
                result = self.result_queue.get(timeout=remaining_time if timeout else None)
                results.append(result)
                self.result_queue.task_done()
                
            except Empty:
                break
        
        return results
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all active tasks to complete.
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            True if all tasks completed, False if timeout
        """
        if not self.active_tasks:
            return True
        
        try:
            # Wait for all futures to complete
            futures = list(self.active_tasks.values())
            
            if not futures:
                return True
            
            logger.info(f"Waiting for {len(futures)} active tasks to complete (timeout: {timeout}s)")
            
            completed_count = 0
            for future in as_completed(futures, timeout=timeout):
                try:
                    future.result()  # This will raise any exceptions
                    completed_count += 1
                    logger.debug(f"Task completed ({completed_count}/{len(futures)})")
                except Exception as e:
                    logger.error(f"Task failed during completion wait: {e}")
                    completed_count += 1  # Count failed tasks as completed
            
            logger.info(f"All {completed_count} tasks completed")
            return True
            
        except Exception as e:
            logger.warning(f"Timeout or error waiting for task completion: {e}")
            
            # Log remaining active tasks
            with self._tasks_lock:
                remaining_tasks = len(self.active_tasks)
                if remaining_tasks > 0:
                    logger.warning(f"{remaining_tasks} tasks still active after timeout")
                    for task_id in list(self.active_tasks.keys())[:5]:  # Log first 5
                        logger.warning(f"  - Still active: {task_id}")
            
            return False
    
    def cancel_all_tasks(self):
        """Cancel all active tasks"""
        with self._tasks_lock:
            cancelled_count = 0
            for task_id, future in self.active_tasks.items():
                if future.cancel():
                    cancelled_count += 1
                    logger.debug(f"Cancelled task {task_id}")
            
            logger.info(f"Cancelled {cancelled_count} active tasks")
            self.active_tasks.clear()
    
    def get_active_task_count(self) -> int:
        """Get number of currently active tasks"""
        with self._tasks_lock:
            return len(self.active_tasks)
    
    def get_active_connection_count(self) -> int:
        """Get number of currently active connections"""
        return self.active_connections.get_value()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get thread manager statistics"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        with self._tasks_lock:
            stats.update({
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'failed_tasks': len(self.failed_tasks),
                'active_connections': self.active_connections.get_value()
            })
        
        return stats
    
    def is_connection_limit_reached(self) -> bool:
        """Check if connection limit is reached"""
        return self.active_connections.get_value() >= self.max_concurrent_connections
    
    def get_available_connections(self) -> int:
        """Get number of available connection slots"""
        return max(0, self.max_concurrent_connections - self.active_connections.get_value())
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop(wait=True, timeout=30.0)