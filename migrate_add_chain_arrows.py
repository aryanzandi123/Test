"""
Database Migration: Add chain_with_arrows JSONB column to interactions table

This migration adds support for displaying typed arrows in interaction chains
(e.g., "VCP --| IκBά --| NF-κB" instead of "VCP → IκBά → NF-κB").

NEW FORMAT (Issue #2):
    chain_with_arrows = [
        {"from": "VCP", "to": "IκBά", "arrow": "inhibits"},
        {"from": "IκBά", "to": "NF-κB", "arrow": "inhibits"}
    ]

BACKWARD COMPATIBILITY:
    - Existing `mediator_chain` and `chain_context` columns preserved
    - New `chain_with_arrows` column nullable (NULL for old data)
    - Frontend checks `chain_with_arrows` first, falls back to generic arrows
    - Backfill not required (will be populated on next query)

Usage:
    python migrate_add_chain_arrows.py
"""

import sys
from app import app, db
from sqlalchemy import text

def migrate():
    """Add chain_with_arrows JSONB column to interactions table."""

    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('interactions')]

            if 'chain_with_arrows' in columns:
                print("✓ Column 'chain_with_arrows' already exists. Migration not needed.")
                return

            print("Adding 'chain_with_arrows' JSONB column to interactions table...")

            # Add the new column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE interactions
                    ADD COLUMN chain_with_arrows JSONB;
                """))
                conn.commit()

            print("✓ Successfully added 'chain_with_arrows' column")

            # Check how many indirect interactions exist
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM interactions
                    WHERE interaction_type = 'indirect'
                      AND mediator_chain IS NOT NULL;
                """))
                indirect_count = result.scalar()
                print(f"\nℹ  Found {indirect_count} indirect interactions")
                print("   These will have chain_with_arrows populated on next query/requery")

            print("\n✅ Migration completed successfully!")
            print("\nNEXT STEPS:")
            print("1. New queries will automatically populate chain_with_arrows")
            print("2. Old indirect interactions will use fallback (generic arrows)")
            print("3. To update old data: re-query proteins with indirect interactors")
            print("\nEXAMPLE:")
            print("  curl -X POST http://localhost:5000/api/query \\")
            print("    -H 'Content-Type: application/json' \\")
            print("    -d '{\"protein\":\"VCP\"}'")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE MIGRATION: Add chain_with_arrows JSONB column (Issue #2)")
    print("=" * 70)
    print()
    print("This migration enables typed arrows in interaction chains.")
    print("Backward compatible: old data shows generic arrows until re-queried.")
    print()

    migrate()
