#!/usr/bin/env python3
"""
Migrate Existing Cache to PostgreSQL

Reads cache/*.json files and populates PostgreSQL database.

Usage:
    python migrate_to_postgres.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

from app import app, db
from utils.db_sync import DatabaseSyncLayer


def find_cache_files() -> List[Path]:
    """
    Find all cache files to migrate.

    Returns:
        List of Path objects for *.json files (excluding *_metadata.json)
    """
    cache_dir = Path("cache")
    if not cache_dir.exists():
        print(f"❌ Cache directory not found: {cache_dir}", file=sys.stderr)
        return []

    # Find all .json files except metadata files
    cache_files = [
        f for f in cache_dir.glob("*.json")
        if not f.name.endswith("_metadata.json")
    ]

    return sorted(cache_files)


def load_cache_data(cache_file: Path) -> Dict:
    """
    Load data from cache file.

    Args:
        cache_file: Path to cache JSON file

    Returns:
        Dict with snapshot_json and optionally ctx_json

    Raises:
        json.JSONDecodeError: If file contains invalid JSON
    """
    # Load main file
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Try to load metadata file (optional)
    metadata_file = cache_file.parent / f"{cache_file.stem}_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                # Merge ctx_json if present
                if "ctx_json" in metadata:
                    data["ctx_json"] = metadata["ctx_json"]
        except json.JSONDecodeError:
            print(f"⚠️  Failed to load metadata file: {metadata_file}", file=sys.stderr)

    return data


def migrate_cache_to_database() -> Dict[str, int]:
    """
    Migrate all cache files to PostgreSQL.

    Returns:
        Stats: {
            "files_processed": int,
            "proteins_migrated": int,
            "interactions_migrated": int,
            "errors": int
        }
    """
    stats = {
        "files_processed": 0,
        "proteins_migrated": 0,
        "interactions_migrated": 0,
        "interactions_updated": 0,
        "errors": 0
    }

    # Find cache files
    cache_files = find_cache_files()
    if not cache_files:
        print("No cache files found to migrate", file=sys.stderr)
        return stats

    print(f"Found {len(cache_files)} cache files to migrate")
    print(f"{'='*80}")

    # Initialize sync layer
    sync_layer = DatabaseSyncLayer()

    # Migrate each file
    for cache_file in cache_files:
        protein_symbol = cache_file.stem
        print(f"\nMigrating {protein_symbol}...", end=" ")

        try:
            # Load data
            data = load_cache_data(cache_file)

            # Extract snapshot_json
            snapshot_json = data.get("snapshot_json", data)
            ctx_json = data.get("ctx_json")

            # Sync to database
            with app.app_context():
                sync_stats = sync_layer.sync_query_results(
                    protein_symbol=protein_symbol,
                    snapshot_json={"snapshot_json": snapshot_json},
                    ctx_json=ctx_json
                )

            # Update stats
            stats["files_processed"] += 1
            stats["proteins_migrated"] += sync_stats["proteins_created"]
            stats["interactions_migrated"] += sync_stats["interactions_created"]
            stats["interactions_updated"] += sync_stats["interactions_updated"]

            # Print result
            print(f"✓ {sync_stats['interactions_created']} new, {sync_stats['interactions_updated']} updated")

        except Exception as e:
            stats["errors"] += 1
            print(f"❌ Failed: {e}", file=sys.stderr)

    return stats


def print_migration_summary(stats: Dict[str, int]):
    """Print migration summary."""
    print(f"\n{'='*80}")
    print("MIGRATION COMPLETE")
    print(f"{'='*80}")
    print(f"Files processed:         {stats['files_processed']}")
    print(f"Proteins migrated:       {stats['proteins_migrated']}")
    print(f"Interactions created:    {stats['interactions_migrated']}")
    print(f"Interactions updated:    {stats['interactions_updated']}")
    print(f"Errors:                  {stats['errors']}")
    print(f"{'='*80}")


def validate_migration() -> bool:
    """
    Validate migration by comparing file count vs database records.

    Returns:
        True if validation passes
    """
    from models import Protein, Interaction

    print(f"\n{'='*80}")
    print("VALIDATION")
    print(f"{'='*80}")

    with app.app_context():
        # Count database records
        protein_count = Protein.query.count()
        interaction_count = Interaction.query.count()

        print(f"Database proteins:       {protein_count}")
        print(f"Database interactions:   {interaction_count}")

        # Count cache files
        cache_files = find_cache_files()
        print(f"Cache files:             {len(cache_files)}")

        # Validation
        if protein_count >= len(cache_files):
            print(f"\n✓ Validation PASSED")
            print(f"  Database has at least as many proteins as cache files")
            return True
        else:
            print(f"\n❌ Validation FAILED")
            print(f"  Database has fewer proteins ({protein_count}) than cache files ({len(cache_files)})")
            return False


def main():
    """Main migration script."""
    print(f"{'='*80}")
    print("CACHE TO POSTGRESQL MIGRATION")
    print(f"{'='*80}\n")

    # Check database connection
    try:
        with app.app_context():
            db.engine.connect()
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}", file=sys.stderr)
        print(f"   Check DATABASE_URL environment variable", file=sys.stderr)
        sys.exit(1)

    # Run migration
    stats = migrate_cache_to_database()

    # Print summary
    print_migration_summary(stats)

    # Validate
    validation_passed = validate_migration()

    # Exit code
    if stats["errors"] > 0 or not validation_passed:
        sys.exit(1)
    else:
        print(f"\n✓ Migration successful!")
        sys.exit(0)


if __name__ == '__main__':
    main()
