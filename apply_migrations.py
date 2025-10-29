#!/usr/bin/env python3
"""
Quick script to apply all pending migrations
Run this once to update your database
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run migrations
from migrations import MigrationRunner

if __name__ == '__main__':
    print("🚀 Applying database migrations...")
    print("This will add the is_admin column and other updates\n")
    
    runner = MigrationRunner()
    runner.run_all_migrations()
    
    print("\n✅ Done! You can now run the application.")

