#!/usr/bin/env python3
"""
Database Migration: Add Chain Metadata Columns to Interactions Table

Adds support for multi-level indirect interactor chains:
- mediator_chain (JSONB) - Full chain path e.g., ["VCP", "LAMP2"]
- depth (INTEGER) - 1=direct, 2=first indirect, 3=second indirect, etc.
- chain_context (JSONB) - Stores interaction from all protein perspectives

Run this script to add chain support:
    python migrate_indirect_chains.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

def run_migration():
    """Add chain metadata columns to interactions table."""

    # Load environment variables
    load_dotenv()

    # Try PUBLIC URL first (for local dev), fall back to internal URL (for Railway deployment)
    database_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ ERROR: DATABASE_PUBLIC_URL or DATABASE_URL not found in .env file")
        print("\n💡 For local development, add DATABASE_PUBLIC_URL to your .env file")
        print("   (Get this from Railway dashboard → Database → Connection → Public URL)")
        sys.exit(1)

    # Show which URL type we're using (without exposing credentials)
    if 'railway.internal' in database_url:
        print("⚠️  Using internal DATABASE_URL (only works from Railway deployment)")
        print("   For local dev, add DATABASE_PUBLIC_URL to .env")
    else:
        print("✓ Using DATABASE_PUBLIC_URL for local connection")

    print("🔧 Database Migration: Adding Chain Metadata Columns")
    print("=" * 60)

    conn = None
    cur = None

    try:
        # Connect to database
        print("📡 Connecting to PostgreSQL database...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Check if columns already exist
        print("\n🔍 Checking existing columns...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'interactions'
        """)
        existing_columns = {row[0] for row in cur.fetchall()}
        print(f"   Found {len(existing_columns)} existing columns")

        columns_to_add = []

        # Check mediator_chain column
        if 'mediator_chain' not in existing_columns:
            columns_to_add.append(('mediator_chain', 'JSONB'))
            print("   ❌ mediator_chain - MISSING")
        else:
            print("   ✅ mediator_chain - exists")

        # Check depth column
        if 'depth' not in existing_columns:
            columns_to_add.append(('depth', 'INTEGER DEFAULT 1 NOT NULL'))
            print("   ❌ depth - MISSING")
        else:
            print("   ✅ depth - exists")

        # Check chain_context column
        if 'chain_context' not in existing_columns:
            columns_to_add.append(('chain_context', 'JSONB'))
            print("   ❌ chain_context - MISSING")
        else:
            print("   ✅ chain_context - exists")

        if not columns_to_add:
            print("\n✅ All chain columns already exist. No migration needed!")
            return

        # Add missing columns
        print(f"\n🔨 Adding {len(columns_to_add)} missing column(s)...")

        for column_name, column_type in columns_to_add:
            print(f"   Adding {column_name} ({column_type})...")
            cur.execute(
                sql.SQL("ALTER TABLE interactions ADD COLUMN {} {}").format(
                    sql.Identifier(column_name),
                    sql.SQL(column_type)
                )
            )

        # Add indexes for performance
        print("\n📊 Creating indexes...")

        # Check if indexes already exist
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'interactions'
        """)
        existing_indexes = {row[0] for row in cur.fetchall()}

        if 'idx_interactions_depth' not in existing_indexes:
            print("   Creating idx_interactions_depth...")
            cur.execute("CREATE INDEX idx_interactions_depth ON interactions(depth)")
        else:
            print("   ✅ idx_interactions_depth - already exists")

        if 'idx_interactions_interaction_type' not in existing_indexes:
            print("   Creating idx_interactions_interaction_type...")
            cur.execute("CREATE INDEX idx_interactions_interaction_type ON interactions(interaction_type)")
        else:
            print("   ✅ idx_interactions_interaction_type - already exists")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify columns were added
        print("\n🔍 Verifying changes...")
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'interactions'
            ORDER BY ordinal_position
        """)
        all_columns = [row[0] for row in cur.fetchall()]

        print(f"\n📋 All columns in interactions table ({len(all_columns)}):")
        for col in all_columns:
            marker = "🆕" if col in [c[0] for c in columns_to_add] else "  "
            print(f"   {marker} {col}")

        # Close connection
        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE")
        print("\nYou can now:")
        print("  1. Restart your Flask app")
        print("  2. Query proteins with max_depth parameter")
        print("  3. Database will store multi-level chain relationships")
        print("  4. Visualizer will render indirect interactions with dashed arrows")

    except psycopg2.Error as e:
        print(f"\n❌ DATABASE ERROR: {e}")
        print("\nRollback performed. Database unchanged.")
        if conn:
            conn.rollback()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  DATABASE MIGRATION SCRIPT")
    print("  Add chain metadata columns for indirect interactors")
    print("=" * 60 + "\n")

    run_migration()
