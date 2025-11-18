"""
Examples of using the task registry programmatically

This file demonstrates how to use the task registry to run tasks in isolation
for testing or direct execution.
"""
from routes.task_registry import (
    get_task_registry,
    run_task,
    run_task_group,
    list_available_tasks
)


def example_run_single_task():
    """Example: Run a single task"""
    print("Running single task: weather:datis")
    result = run_task('weather:datis')
    print(f"Result: {result}")


def example_run_task_group():
    """Example: Run a task group"""
    print("Running task group: weather:all")
    results = run_task_group('weather:all')
    print(f"Results: {results}")


def example_run_multiple_tasks():
    """Example: Run multiple specific tasks"""
    registry = get_task_registry()
    task_names = ['weather:datis', 'gate:fetch', 'test:jms']
    
    print(f"Running multiple tasks: {', '.join(task_names)}")
    results = registry.run_tasks(task_names)
    
    for task_name, result in results.items():
        print(f"{task_name}: {result}")


def example_list_all_tasks():
    """Example: List all available tasks"""
    tasks = list_available_tasks()
    print("Available tasks:")
    for task in tasks:
        print(f"  - {task}")


def example_direct_handler_access():
    """Example: Access handlers directly (for advanced use cases)"""
    from routes.task_handlers import WeatherTaskHandlers, GateTaskHandlers
    
    # Direct access to handlers
    weather_handler = WeatherTaskHandlers()
    gate_handler = GateTaskHandlers()
    
    # You can call methods directly (but need to handle async manually)
    import asyncio
    result = asyncio.run(weather_handler.fetch_datis())
    print(f"Direct handler result: {result}")


if __name__ == '__main__':
    print("=" * 60)
    print("Task Registry Examples")
    print("=" * 60)
    
    print("\n1. List all available tasks:")
    example_list_all_tasks()
    
    print("\n2. Run a single task (commented out to avoid actual execution):")
    print("# example_run_single_task()")
    
    print("\n3. Run a task group (commented out to avoid actual execution):")
    print("# example_run_task_group()")
    
    print("\n4. Run multiple tasks (commented out to avoid actual execution):")
    print("# example_run_multiple_tasks()")
    
    print("\n" + "=" * 60)
    print("Uncomment the examples above to run them")
    print("=" * 60)

