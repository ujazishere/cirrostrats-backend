"""
Task Runner for Testing

This script demonstrates how to run individual tasks or task groups in isolation
for testing purposes, without going through Celery.

Usage examples:
    # Run a single task
    python -m routes.test_task_runner weather:datis
    
    # Run a task group
    python -m routes.test_task_runner weather:all
    
    # Run multiple tasks
    python -m routes.test_task_runner weather:datis gate:fetch test:jms
    
    # List all available tasks
    python -m routes.test_task_runner --list
    
    # List all task groups
    python -m routes.test_task_runner --list-groups
"""
import sys
import argparse
from routes.task_registry import (
    get_task_registry,
    list_available_tasks,
    list_available_groups
)


def main():
    parser = argparse.ArgumentParser(
        description='Run Celery tasks in isolation for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'tasks',
        nargs='*',
        help='Task names or task group names to run (e.g., weather:datis, weather:all)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tasks'
    )
    
    parser.add_argument(
        '--list-groups',
        action='store_true',
        help='List all available task groups'
    )
    
    args = parser.parse_args()
    
    registry = get_task_registry()
    
    if args.list:
        print("Available tasks:")
        for task in list_available_tasks():
            print(f"  - {task}")
        return
    
    if args.list_groups:
        print("Available task groups:")
        for group in list_available_groups():
            tasks = registry.task_groups[group]
            print(f"  - {group}: {', '.join(tasks)}")
        return
    
    if not args.tasks:
        parser.print_help()
        print("\nExamples:")
        print("  python -m routes.test_task_runner weather:datis")
        print("  python -m routes.test_task_runner weather:all")
        print("  python -m routes.test_task_runner weather:datis gate:fetch")
        return
    
    # Run tasks
    results = {}
    
    for task_name in args.tasks:
        try:
            # Check if it's a task group
            if task_name in registry.task_groups:
                print(f"\n{'='*60}")
                print(f"Running task group: {task_name}")
                print(f"{'='*60}")
                results[task_name] = registry.run_task_group(task_name)
            else:
                print(f"\n{'='*60}")
                print(f"Running task: {task_name}")
                print(f"{'='*60}")
                results[task_name] = registry.run_task(task_name)
        except KeyError as e:
            print(f"\nError: {e}")
            results[task_name] = {'error': str(e)}
        except Exception as e:
            print(f"\nUnexpected error running '{task_name}': {e}")
            import traceback
            traceback.print_exc()
            results[task_name] = {'error': str(e)}
    
    # Print summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for task_name, result in results.items():
        if isinstance(result, dict) and 'error' in result:
            print(f"  {task_name}: FAILED - {result['error']}")
        else:
            print(f"  {task_name}: SUCCESS")
            if isinstance(result, dict) and len(result) <= 3:
                # Print small results inline
                print(f"    Result: {result}")


if __name__ == '__main__':
    main()

