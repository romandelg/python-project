"""
Launcher script for the synthesizer application.
Run this script from the project root directory.
"""
import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'src'))

# Import and run the main application
from src.main import main

if __name__ == "__main__":
    main()
