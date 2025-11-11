#!/usr/bin/env python3
"""
Sync Existing File Cache to PostgreSQL Database

This script reads existing cached protein data and syncs it to the database.
Use this to populate the database WITHOUT re-running the entire pipeline.

Usage:
    python sync_cache_to_db.py p62
    python sync_cache_to_db.py ATXN3
    python sync_cache_to_db.py --all  # sync all cached proteins
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app
from models import db
from utils.db_sync import DatabaseSyncLayer

def load_cache_file(protein_symbol):
    """Load protein data from file cache."""
    cache_file = Path(f"cache/{protein_symbol}.json")

    if not cache_file.exists():
        print(f"[ERROR] Cache file not found: {cache_file}")
        return None

    print(f"[LOAD] Loading cache file: {cache_file}")

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if 'snapshot_json' not in data:
            print(f"[WARN] Warning: No snapshot_json in cache file")
            return None

        return data

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in cache file: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error reading cache file: {e}")
        return None

def sync_protein_to_db(protein_symbol):
    """Sync a single protein from file cache to database."""

    print("\n" + "=" * 70)
    print(f"  Syncing {protein_symbol.upper()} to Database")
    print("=" * 70 + "\n")

    # Load cache data
    cache_data = load_cache_file(protein_symbol)
    if not cache_data:
        return False

    # Extract components
    snapshot_json = cache_data.get('snapshot_json', {})
    ctx_json = cache_data.get('ctx_json')

    if not snapshot_json:
        print("[ERROR] No snapshot_json data to sync")
        return False

    # Get interactor count
    interactors = snapshot_json.get('interactors', [])
    print(f"[INFO] Found {len(interactors)} interactors in cache")

    # Initialize sync layer
    with app.app_context():
        sync_layer = DatabaseSyncLayer()

        try:
            print("\n[SYNC] Syncing to database...")

            # Sync to database
            stats = sync_layer.sync_query_results(
                protein_symbol=protein_symbol,
                snapshot_json={'snapshot_json': snapshot_json},
                ctx_json=ctx_json
            )

            # Print results
            print("\n[OK] Sync completed successfully!")
            print("\n[STATS] Database Stats:")
            print(f"   Protein: {protein_symbol}")
            print(f"   Proteins created: {stats.get('proteins_created', 0)}")
            print(f"   Interactions created: {stats.get('interactions_created', 0)}")
            print(f"   Interactions updated: {stats.get('interactions_updated', 0)}")
            print(f"   Total: {stats.get('interactions_created', 0) + stats.get('interactions_updated', 0)}")

            return True

        except Exception as e:
            print(f"\n[ERROR] Database sync failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def sync_all_cached_proteins():
    """Sync all proteins found in cache directory."""

    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("[ERROR] Cache directory not found")
        return

    # Find all JSON files in cache (exclude pruned subdirectory)
    cache_files = list(cache_dir.glob("*.json"))

    if not cache_files:
        print("[ERROR] No cache files found")
        return

    print(f"\n[INFO] Found {len(cache_files)} cached protein(s)")

    success_count = 0
    fail_count = 0

    for cache_file in cache_files:
        protein_symbol = cache_file.stem  # filename without .json

        if sync_protein_to_db(protein_symbol):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("  SYNC SUMMARY")
    print("=" * 70)
    print(f"  [OK] Successfully synced: {success_count}")
    print(f"  [FAIL] Failed: {fail_count}")
    print(f"  [TOTAL] Total: {len(cache_files)}")
    print("=" * 70 + "\n")

def main():
    """Main entry point."""

    # Load environment
    load_dotenv()

    # Check DATABASE_URL (app.py will prefer DATABASE_PUBLIC_URL if available)
    database_url = os.getenv('DATABASE_PUBLIC_URL') or os.getenv('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_PUBLIC_URL or DATABASE_URL not found in .env file")
        print("\n[TIP] For local development, add DATABASE_PUBLIC_URL to your .env file")
        print("   (Get this from Railway dashboard > Database > Connection > Public URL)")
        sys.exit(1)

    # Show which URL type we're using
    if 'railway.internal' in database_url:
        print("[!] Using internal DATABASE_URL (only works from Railway deployment)")
        print("   For local dev, add DATABASE_PUBLIC_URL to .env\n")
    else:
        print("[OK] Using DATABASE_PUBLIC_URL for local connection\n")

    # Parse arguments
    if len(sys.argv) < 2:
        print("\n[ERROR] Usage: python sync_cache_to_db.py <protein_symbol>")
        print("   Examples:")
        print("     python sync_cache_to_db.py p62")
        print("     python sync_cache_to_db.py ATXN3")
        print("     python sync_cache_to_db.py --all")
        sys.exit(1)

    protein_arg = sys.argv[1]

    if protein_arg == '--all':
        sync_all_cached_proteins()
    else:
        success = sync_protein_to_db(protein_arg)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
