"""
Convenience runner for Computer Lockdown.

Run this script from the project root to start the application without
installing it as a package::

    python run.py
    python run.py --reset    # wipe all config, logs, and cached data
"""

import os
import sys

# Ensure the project root is on sys.path so that ``from src.…`` imports work
# regardless of the working directory the user invoked the script from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if "--reset" in sys.argv:
    from src.cleanup import full_cleanup
    full_cleanup()
else:
    from src.main import main
    main()
