"""
Database Migration: Add arrows JSONB column to interactions table

This migration adds support for multiple arrow types per protein pair by adding
a new JSONB column that stores arrows grouped by direction.

NEW FORMAT (Issue #4):
    arrows = {
        'main_to_primary': ['activates', 'inhibits'],  # Query → Interactor
        'primary_to_main': ['binds'],                  # Interactor → Query
        'bidirectional': ['complex']                   # Both directions
    }

BACKWARD COMPATIBILITY:
    - Existing `arrow` column preserved (VARCHAR)
    - New `arrows` column nullable (NULL for old data)
    - Frontend checks `arrows` first, falls back to `arrow`

Usage:
    python migrate_add_arrows.py
"""

import sys
from app import app, db
from sqlalchemy import text

def migrate():
    """Add arrows JSONB column to interactions table."""

    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('interactions')]

            if 'arrows' in columns:
                print("✓ Column 'arrows' already exists. Migration not needed.")
                return

            print("Adding 'arrows' JSONB column to interactions table...")

            # Add the new column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE interactions
                    ADD COLUMN arrows JSONB;
                """))
                conn.commit()

            print("✓ Successfully added 'arrows' column")

            # Optional: Populate initial values for existing rows
            print("\nPopulating initial values for backward compatibility...")
            with db.engine.connect() as conn:
                # Convert existing arrow column to arrows dict format
                # Example: arrow='activates' → arrows={'main_to_primary': ['activates']}
                result = conn.execute(text("""
                    UPDATE interactions
                    SET arrows = jsonb_build_object(
                        'main_to_primary',
                        jsonb_build_array(COALESCE(arrow, 'binds'))
                    )
                    WHERE arrows IS NULL AND arrow IS NOT NULL;
                """))
                conn.commit()
                print(f"✓ Migrated {result.rowcount} existing rows to new format")

            # Leave arrows=NULL for rows with no arrow data
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM interactions WHERE arrows IS NULL;
                """))
                null_count = result.scalar()
                if null_count > 0:
                    print(f"ℹ  {null_count} rows have arrows=NULL (will use fallback logic)")

            print("\n✅ Migration completed successfully!")
            print("\nNEXT STEPS:")
            print("1. New queries will use new arrow determination logic")
            print("2. Old proteins keep existing data (gradual migration)")
            print("3. Frontend will check 'arrows' first, fall back to 'arrow'")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE MIGRATION: Add arrows JSONB column (Issue #4)")
    print("=" * 70)
    print()
    print("This migration enables multiple arrow types per protein pair.")
    print("Backward compatible: existing data will be converted automatically.")
    print()

    migrate()
