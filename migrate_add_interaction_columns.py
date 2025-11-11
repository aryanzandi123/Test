#!/usr/bin/env python3
"""
Database Migration: Add Missing Columns to Interactions Table

Adds 5 missing columns:
- interaction_type (VARCHAR(20)) - 'direct' or 'indirect'
- upstream_interactor (VARCHAR(50)) - for indirect interactions
- mediator_chain (JSONB) - full chain path (e.g., ["VCP", "LAMP2"])
- depth (INTEGER DEFAULT 1 NOT NULL) - number of hops from query protein
- chain_context (JSONB) - stores full chain context from all perspectives

Adds 2 missing indexes:
- idx_interactions_depth - index on depth column
- idx_interactions_interaction_type - index on interaction_type column

Run this script to fix the schema mismatch error:
    python migrate_add_interaction_columns.py
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

def run_migration():
    """Add missing columns to interactions table."""

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

    print("🔧 Database Migration: Adding Missing Columns")
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

        # Check interaction_type column
        if 'interaction_type' not in existing_columns:
            columns_to_add.append(('interaction_type', 'VARCHAR(20)', 'NULL'))
            print("   ❌ interaction_type - MISSING")
        else:
            print("   ✅ interaction_type - exists")

        # Check upstream_interactor column
        if 'upstream_interactor' not in existing_columns:
            columns_to_add.append(('upstream_interactor', 'VARCHAR(50)', 'NULL'))
            print("   ❌ upstream_interactor - MISSING")
        else:
            print("   ✅ upstream_interactor - exists")

        # Check mediator_chain column
        if 'mediator_chain' not in existing_columns:
            columns_to_add.append(('mediator_chain', 'JSONB', 'NULL'))
            print("   ❌ mediator_chain - MISSING")
        else:
            print("   ✅ mediator_chain - exists")

        # Check depth column
        if 'depth' not in existing_columns:
            columns_to_add.append(('depth', 'INTEGER', 'DEFAULT 1 NOT NULL'))
            print("   ❌ depth - MISSING")
        else:
            print("   ✅ depth - exists")

        # Check chain_context column
        if 'chain_context' not in existing_columns:
            columns_to_add.append(('chain_context', 'JSONB', 'NULL'))
            print("   ❌ chain_context - MISSING")
        else:
            print("   ✅ chain_context - exists")

        if not columns_to_add:
            print("\n✅ All columns already exist. Checking indexes...")
        else:
            # Add missing columns
            print(f"\n🔨 Adding {len(columns_to_add)} missing column(s)...")

            for column_name, column_type, constraints in columns_to_add:
                print(f"   Adding {column_name} ({column_type} {constraints})...")
                cur.execute(
                    sql.SQL("ALTER TABLE interactions ADD COLUMN {} {} {}").format(
                        sql.Identifier(column_name),
                        sql.SQL(column_type),
                        sql.SQL(constraints)
                    )
                )

        # Check and create indexes
        print("\n🔍 Checking indexes...")
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'interactions'
        """)
        existing_indexes = {row[0] for row in cur.fetchall()}

        indexes_to_create = []

        # Check idx_interactions_depth
        if 'idx_interactions_depth' not in existing_indexes:
            indexes_to_create.append(('idx_interactions_depth', 'depth'))
            print("   ❌ idx_interactions_depth - MISSING")
        else:
            print("   ✅ idx_interactions_depth - exists")

        # Check idx_interactions_interaction_type
        if 'idx_interactions_interaction_type' not in existing_indexes:
            indexes_to_create.append(('idx_interactions_interaction_type', 'interaction_type'))
            print("   ❌ idx_interactions_interaction_type - MISSING")
        else:
            print("   ✅ idx_interactions_interaction_type - exists")

        if indexes_to_create:
            print(f"\n🔨 Creating {len(indexes_to_create)} missing index(es)...")
            for index_name, column_name in indexes_to_create:
                print(f"   Creating {index_name} on {column_name}...")
                cur.execute(
                    sql.SQL("CREATE INDEX {} ON interactions({})").format(
                        sql.Identifier(index_name),
                        sql.Identifier(column_name)
                    )
                )
        else:
            print("\n✅ All indexes already exist.")

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
        added_col_names = [c[0] for c in columns_to_add]
        for col in all_columns:
            marker = "🆕" if col in added_col_names else "  "
            print(f"   {marker} {col}")

        # Verify indexes
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'interactions'
            ORDER BY indexname
        """)
        all_indexes = [row[0] for row in cur.fetchall()]

        print(f"\n📋 All indexes on interactions table ({len(all_indexes)}):")
        added_index_names = [idx[0] for idx in indexes_to_create]
        for idx in all_indexes:
            marker = "🆕" if idx in added_index_names else "  "
            print(f"   {marker} {idx}")

        # Close connection
        cur.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE")
        print("\nYou can now:")
        print("  1. Restart your Flask app")
        print("  2. Query p62 to test visualization")
        print("  3. Database sync will now work correctly")

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
    print("\n" + "=" * 70)
    print("  DATABASE MIGRATION SCRIPT")
    print("  Add 5 missing columns + 2 indexes to interactions table")
    print("=" * 70 + "\n")

    run_migration()
