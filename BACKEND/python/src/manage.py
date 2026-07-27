#!/usr/bin/env python
"""
DEVS PROJECT ENGINE: 
This is the command-line utility for administrative tasks.
It acts as the gateway for migrations, server initialization, and testing.
"""
import os
import sys

def setup_devs_groups():
    """
    PHASE 1: GROUP-BASED ROLES & LOGIC
    Categorizes users into Clerk, Advocate, and Judge groups.
    """
    try:
        import django
        django.setup()
        from django.contrib.auth.models import Group
        
        groups = ['Clerk', 'Advocate', 'Admin']
        print("--- Initializing DEVS Group Setup ---")
        
        for group_name in groups:
            new_group, created = Group.objects.get_or_create(name=group_name)
            if created:
                print(f"Group '{group_name}' created successfully.")
            else:
                print(f"Group '{group_name}' already exists.")
        print("--- Setup Complete ---\n")
        
    except Exception as e:
        print(f"Error during group initialization: {e}")

def main():
    """
    CORE INITIALIZATION:
    Sets the project settings and executes commands passed via the terminal.
    """
    # Points Django to the specific configuration file for the Forensic System.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DEVS_PROJECT.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Custom Trigger: If you run 'python manage.py setup_groups'
    if len(sys.argv) > 1 and sys.argv[1] == 'setup_groups':
        setup_devs_groups()
        return # Exit after setup so it doesn't try to find a Django command named 'setup_groups'

    # Standard execution: This is what processes 'runserver' or 'migrate'.
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()