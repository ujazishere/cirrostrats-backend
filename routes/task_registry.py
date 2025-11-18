"""
Task Registry Module

This module provides utilities for running tasks in isolation for testing purposes.
It allows you to execute individual task handlers or groups of tasks without
going through Celery.
"""
import asyncio
import logging
from typing import Dict, Callable, Any, List, Optional

from routes.task_handlers import (
    WeatherTaskHandlers,
    GateTaskHandlers,
    NASTaskHandlers,
    TestingTaskHandlers
)

logger = logging.getLogger(__name__)


class TaskRegistry:
    """
    Registry for all task handlers, allowing them to be run in isolation
    for testing or direct execution.
    """
    
    def __init__(self):
        self.weather_handlers = WeatherTaskHandlers()
        self.gate_handlers = GateTaskHandlers()
        self.nas_handlers = NASTaskHandlers()
        self.testing_handlers = TestingTaskHandlers()
        
        # Register all tasks
        self._register_tasks()
    
    def _register_tasks(self):
        """Register all available tasks"""
        self.tasks: Dict[str, Callable] = {
            # Weather tasks
            'weather:datis': self._run_async(self.weather_handlers.fetch_datis),
            'weather:metar': self._run_async(self.weather_handlers.fetch_metar),
            'weather:taf': self._run_async(self.weather_handlers.fetch_taf),
            
            # Gate tasks
            'gate:fetch': self.gate_handlers.fetch_gates,
            'gate:recurrent': self.gate_handlers.update_gates_recurrent,
            'gate:clear': self.gate_handlers.clear_historical_gates,
            
            # NAS tasks
            'nas:fetch': self.nas_handlers.fetch_and_monitor_nas,
            
            # Testing tasks
            'test:all': self.testing_handlers.run_all_tests,
            'test:jms': self.testing_handlers.run_jms_test,
            'test:weather': self.testing_handlers.run_weather_test,
            'test:fs': self._run_async(self.testing_handlers.run_fs_test_isolated),
        }
        
        # Task groups for running multiple related tasks
        self.task_groups: Dict[str, List[str]] = {
            'weather:all': ['weather:datis', 'weather:metar', 'weather:taf'],
            'gate:all': ['gate:fetch', 'gate:recurrent'],
            'test:core': ['test:jms', 'test:weather'],
        }
    
    @staticmethod
    def _run_async(async_func: Callable) -> Callable:
        """Wrapper to run async functions synchronously"""
        def wrapper(*args, **kwargs):
            return asyncio.run(async_func(*args, **kwargs))
        return wrapper
    
    def list_tasks(self) -> List[str]:
        """List all available task names"""
        return list(self.tasks.keys())
    
    def list_task_groups(self) -> List[str]:
        """List all available task group names"""
        return list(self.task_groups.keys())
    
    def run_task(self, task_name: str, *args, **kwargs) -> Any:
        """
        Run a single task by name
        
        Args:
            task_name: Name of the task to run (e.g., 'weather:datis')
            *args: Positional arguments to pass to the task
            **kwargs: Keyword arguments to pass to the task
            
        Returns:
            Result from the task execution
            
        Raises:
            KeyError: If task_name is not found
        """
        if task_name not in self.tasks:
            available = ', '.join(self.list_tasks())
            raise KeyError(
                f"Task '{task_name}' not found. Available tasks: {available}"
            )
        
        logger.info(f"Running task: {task_name}")
        try:
            result = self.tasks[task_name](*args, **kwargs)
            logger.info(f"Task '{task_name}' completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task '{task_name}' failed: {str(e)}", exc_info=True)
            raise
    
    def run_task_group(self, group_name: str) -> Dict[str, Any]:
        """
        Run a group of tasks
        
        Args:
            group_name: Name of the task group to run (e.g., 'weather:all')
            
        Returns:
            Dictionary mapping task names to their results
            
        Raises:
            KeyError: If group_name is not found
        """
        if group_name not in self.task_groups:
            available = ', '.join(self.list_task_groups())
            raise KeyError(
                f"Task group '{group_name}' not found. Available groups: {available}"
            )
        
        task_names = self.task_groups[group_name]
        results = {}
        
        logger.info(f"Running task group: {group_name} ({len(task_names)} tasks)")
        
        for task_name in task_names:
            try:
                results[task_name] = self.run_task(task_name)
            except Exception as e:
                logger.error(f"Task '{task_name}' in group '{group_name}' failed: {str(e)}")
                results[task_name] = {'error': str(e)}
        
        return results
    
    def run_tasks(self, task_names: List[str]) -> Dict[str, Any]:
        """
        Run multiple tasks by name
        
        Args:
            task_names: List of task names to run
            
        Returns:
            Dictionary mapping task names to their results
        """
        results = {}
        
        logger.info(f"Running {len(task_names)} tasks: {', '.join(task_names)}")
        
        for task_name in task_names:
            try:
                results[task_name] = self.run_task(task_name)
            except Exception as e:
                logger.error(f"Task '{task_name}' failed: {str(e)}")
                results[task_name] = {'error': str(e)}
        
        return results


# Global registry instance
_registry: Optional[TaskRegistry] = None


def get_task_registry() -> TaskRegistry:
    """Get or create the global task registry instance"""
    global _registry
    if _registry is None:
        _registry = TaskRegistry()
    return _registry


# Convenience functions for direct usage
def run_task(task_name: str, *args, **kwargs) -> Any:
    """Run a single task by name"""
    return get_task_registry().run_task(task_name, *args, **kwargs)


def run_task_group(group_name: str) -> Dict[str, Any]:
    """Run a task group by name"""
    return get_task_registry().run_task_group(group_name)


def list_available_tasks() -> List[str]:
    """List all available tasks"""
    return get_task_registry().list_tasks()


def list_available_groups() -> List[str]:
    """List all available task groups"""
    return get_task_registry().list_task_groups()

