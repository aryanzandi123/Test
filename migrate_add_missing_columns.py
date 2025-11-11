#!/usr/bin/env python3
"""
Migration: Add missing columns to interactions table

Adds columns that exist in models.py but not in the PostgreSQL database:
- arrows (JSONB) - Multiple arrow types per direction
- interaction_type (VARCHAR) - 'direct' or 'indirect'
- upstream_interactor (VARCHAR) - Upstream protein for indirect interactions
- function_context (VARCHAR) - 'direct', 'chain', or 'mixed'
- mediator_chain (JSONB) - Full chain path for multi-hop interactions
- depth (INTEGER) - Number of hops from query protein
- chain_context (JSONB) - Full chain context from all perspectives
- chain_with_arrows (JSONB) - Chain with typed arrows

Run: python migrate_add_missing_columns.py
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get raw psycopg2 connection for DDL operations"""
    # Prefer DATABASE_PUBLIC_URL for local development
    database_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL or DATABASE_PUBLIC_URL not set in .env")
    return psycopg2.connect(database_url)

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s
            AND column_name = %s
        );
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def migrate():
    """Add missing columns to interactions table"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("MIGRATION: Adding missing columns to interactions table")
        print("=" * 60)

        # Define columns to add with their SQL definitions
        columns_to_add = [
            ('arrows', 'JSONB', None),
            ('interaction_type', 'VARCHAR(20)', None),
            ('upstream_interactor', 'VARCHAR(50)', None),
            ('function_context', 'VARCHAR(20)', None),
            ('mediator_chain', 'JSONB', None),
            ('depth', 'INTEGER', '1'),  # Default to 1 for existing rows
            ('chain_context', 'JSONB', None),
            ('chain_with_arrows', 'JSONB', None),
        ]

        added = []
        skipped = []

        for col_name, col_type, default_value in columns_to_add:
            if column_exists(cursor, 'interactions', col_name):
                print(f"[SKIP] Column '{col_name}' already exists, skipping")
                skipped.append(col_name)
                continue

            # Build ALTER TABLE statement
            alter_sql = f"ALTER TABLE interactions ADD COLUMN {col_name} {col_type}"
            if default_value is not None:
                alter_sql += f" DEFAULT {default_value}"
            alter_sql += ";"

            print(f"[ADD] Adding column '{col_name}' ({col_type})...")
            cursor.execute(alter_sql)
            added.append(col_name)

        # Commit all changes
        conn.commit()

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print(f"[OK] Added {len(added)} column(s): {', '.join(added) if added else '(none)'}")
        print(f"[SKIP] Skipped {len(skipped)} column(s): {', '.join(skipped) if skipped else '(none)'}")
        print("\n[SUCCESS] You can now restart app.py")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrate()
