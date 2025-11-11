"""
Database Migration: Add function_context column to interactions table

This migration adds support for context-aware function display by adding
a new column to track whether functions are from direct pair interactions
or chain context.

Usage:
    python migrate_add_function_context.py
"""

import sys
from app import app, db
from sqlalchemy import text

def migrate():
    """Add function_context column to interactions table."""

    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('interactions')]

            if 'function_context' in columns:
                print("✓ Column 'function_context' already exists. Migration not needed.")
                return

            print("Adding 'function_context' column to interactions table...")

            # Add the new column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE interactions
                    ADD COLUMN function_context VARCHAR(20);
                """))
                conn.commit()

            print("✓ Successfully added 'function_context' column")

            # Optional: Populate initial values based on existing data
            print("\nPopulating initial values...")
            with db.engine.connect() as conn:
                # Default to 'direct' for existing interactions
                # Can be updated later based on function analysis
                result = conn.execute(text("""
                    UPDATE interactions
                    SET function_context = 'direct'
                    WHERE function_context IS NULL;
                """))
                conn.commit()
                print(f"✓ Updated {result.rowcount} rows with default value 'direct'")

            print("\n✅ Migration completed successfully!")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE MIGRATION: Add function_context column")
    print("=" * 70)
    print()

    migrate()
