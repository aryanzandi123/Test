#!/usr/bin/env python3
"""
Cache Migration Script

Migrates from old query-centric cache format to new protein-centric database.

Old format:
    cache/
        ATXN3.json          (snapshot_json only)
        ATXN3_metadata.json (ctx_json with rich data)
        VCP.json
        VCP_metadata.json

New format:
    cache/
        proteins/
            ATXN3/
                metadata.json
                interactions/
                    VCP.json
                    HDAC6.json
            VCP/
                metadata.json
                interactions/
                    ATXN3.json (symmetric)
                    UFD1L.json

Usage:
    python migrate_cache.py [--dry-run] [--archive]
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set

import utils.protein_database as db


def find_old_cache_files(cache_dir: Path) -> List[str]:
    """
    Find all protein cache files in old format.

    Returns list of protein names (e.g., ["ATXN3", "VCP"])
    """
    proteins = []

    for file in cache_dir.glob("*.json"):
        # Skip metadata files and other files
        if file.stem.endswith("_metadata"):
            continue
        if file.stem.startswith("."):
            continue
        if file.name == "interactions.json":  # Skip if exists
            continue

        # This is a protein cache file
        proteins.append(file.stem)

    return sorted(proteins)


def load_old_cache_data(protein: str, cache_dir: Path) -> Dict[str, Any]:
    """
    Load both snapshot and metadata from old cache format.

    Returns:
        Dict with 'snapshot_json' and optionally 'ctx_json'
    """
    snapshot_file = cache_dir / f"{protein}.json"
    metadata_file = cache_dir / f"{protein}_metadata.json"

    result = {}

    # Load snapshot (required)
    if snapshot_file.exists():
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
            result['snapshot_json'] = snapshot_data.get('snapshot_json', snapshot_data)

    # Load metadata (optional)
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_data = json.load(f)
            result['ctx_json'] = metadata_data.get('ctx_json', {})

    return result


def migrate_protein(
    protein: str,
    cache_dir: Path,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Migrate a single protein from old to new format.

    Args:
        protein: Protein symbol
        cache_dir: Path to old cache directory
        dry_run: If True, don't actually write files

    Returns:
        Stats dict with counts
    """
    stats = {
        "interactions_saved": 0,
        "interactions_skipped": 0,
        "errors": 0
    }

    print(f"\n{'='*80}")
    print(f"Migrating: {protein}")
    print(f"{'='*80}")

    # Load old cache data
    old_data = load_old_cache_data(protein, cache_dir)

    if not old_data or 'snapshot_json' not in old_data:
        print(f"  WARNING: No snapshot_json found for {protein}")
        stats["errors"] += 1
        return stats

    snapshot = old_data['snapshot_json']
    main_protein = snapshot.get('main', protein)
    interactors = snapshot.get('interactors', [])

    print(f"  Found {len(interactors)} interactors")

    if not interactors:
        print(f"  WARNING: No interactors to migrate")
        return stats

    # Migrate each interaction
    for interactor in interactors:
        partner = interactor.get('primary')
        if not partner:
            print(f"    WARNING: Skipping interactor without 'primary' field")
            stats["interactions_skipped"] += 1
            continue

        # Check if this interaction already exists in new database
        if not dry_run and db._interaction_file_path(main_protein, partner).exists():
            print(f"    Already exists: {main_protein} <-> {partner}")
            stats["interactions_skipped"] += 1
            continue

        if dry_run:
            print(f"    [DRY RUN] Would save: {main_protein} <-> {partner}")
            stats["interactions_saved"] += 1
        else:
            # Save interaction using database layer
            success = db.save_interaction(main_protein, partner, interactor)
            if success:
                print(f"    Saved: {main_protein} <-> {partner}")
                stats["interactions_saved"] += 1
            else:
                print(f"    Failed: {main_protein} <-> {partner}")
                stats["errors"] += 1

    # Update protein metadata
    if not dry_run:
        db.update_protein_metadata(main_protein, query_completed=True)
        print(f"  [OK] Updated metadata for {main_protein}")

    return stats


def validate_migration(proteins: List[str], cache_dir: Path) -> bool:
    """
    Validate that migration preserved all data.

    Checks:
    - All proteins migrated
    - All interactions migrated
    - Symmetric interactions exist
    - No data loss

    Returns:
        True if validation passes
    """
    print(f"\n{'='*80}")
    print("VALIDATION")
    print(f"{'='*80}")

    all_valid = True

    for protein in proteins:
        old_data = load_old_cache_data(protein, cache_dir)
        if not old_data or 'snapshot_json' not in old_data:
            continue

        old_interactors = old_data['snapshot_json'].get('interactors', [])
        old_partners = {i.get('primary') for i in old_interactors if i.get('primary')}

        # Check new database
        new_interactions = db.get_all_interactions(protein)
        new_partners = {i.get('primary') for i in new_interactions if i.get('primary')}

        if old_partners != new_partners:
            print(f"  [ERROR] {protein}: Partner mismatch")
            print(f"      Old: {sorted(old_partners)}")
            print(f"      New: {sorted(new_partners)}")
            all_valid = False
        else:
            print(f"  [OK] {protein}: {len(old_partners)} interactions verified")

        # Check symmetric interactions exist
        for partner in old_partners:
            symmetric_file = db._interaction_file_path(partner, protein)
            if not symmetric_file.exists():
                print(f"    [WARNING] Missing symmetric: {partner}/interactions/{protein}.json")
                all_valid = False

    return all_valid


def archive_old_cache(cache_dir: Path) -> bool:
    """
    Archive old cache to cache_old/ directory.

    Returns:
        True on success
    """
    archive_dir = cache_dir.parent / "cache_old"

    try:
        # Create archive directory
        archive_dir.mkdir(exist_ok=True)

        # Move old cache files
        for file in cache_dir.glob("*.json"):
            if file.stem.startswith("."):
                continue
            if file.parent.name == "proteins":  # Don't archive new database
                continue

            # Copy to archive
            archive_file = archive_dir / file.name
            shutil.copy2(file, archive_file)
            print(f"  Archived: {file.name}")

        print(f"\n[OK] Old cache archived to: {archive_dir}")
        return True

    except Exception as e:
        print(f"\n[ERROR] Archive failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Migrate cache from old query-centric to new protein-centric format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually doing it"
    )
    parser.add_argument(
        "--archive",
        action="store_true",
        help="Archive old cache files after successful migration"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache"),
        help="Path to cache directory (default: ./cache)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation, don't migrate"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-confirm migration (skip interactive prompt)"
    )

    args = parser.parse_args()

    cache_dir = args.cache_dir
    if not cache_dir.exists():
        print(f"[ERROR] Cache directory not found: {cache_dir}")
        return 1

    print(f"\n{'='*80}")
    print("PROTEIN INTERACTION DATABASE MIGRATION")
    print(f"{'='*80}")
    print(f"Cache directory: {cache_dir.absolute()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"{'='*80}")

    # Find proteins in old cache
    proteins = find_old_cache_files(cache_dir)

    if not proteins:
        print("\n[ERROR] No proteins found in old cache format")
        print(f"   Looking for: {cache_dir}/<PROTEIN>.json")
        return 1

    print(f"\nFound {len(proteins)} proteins to migrate:")
    for protein in proteins:
        print(f"  - {protein}")

    if args.validate_only:
        # Just run validation
        if not db.database_exists():
            print("\n[ERROR] New database doesn't exist yet. Run migration first.")
            return 1
        valid = validate_migration(proteins, cache_dir)
        return 0 if valid else 1

    # Confirm before proceeding (unless dry run or --yes)
    if not args.dry_run and not args.yes:
        print(f"\nWARNING: This will create a new protein-centric database structure.")
        print(f"   The old cache files will NOT be deleted (use --archive to archive them).")
        response = input("\nProceed with migration? [y/N]: ")
        if response.lower() != 'y':
            print("Migration cancelled.")
            return 0

    # Migrate each protein
    total_stats = {
        "proteins_processed": 0,
        "interactions_saved": 0,
        "interactions_skipped": 0,
        "errors": 0
    }

    for protein in proteins:
        stats = migrate_protein(protein, cache_dir, dry_run=args.dry_run)
        total_stats["proteins_processed"] += 1
        total_stats["interactions_saved"] += stats["interactions_saved"]
        total_stats["interactions_skipped"] += stats["interactions_skipped"]
        total_stats["errors"] += stats["errors"]

    # Print summary
    print(f"\n{'='*80}")
    print("MIGRATION SUMMARY")
    print(f"{'='*80}")
    print(f"Proteins processed:       {total_stats['proteins_processed']}")
    print(f"Interactions saved:       {total_stats['interactions_saved']}")
    print(f"Interactions skipped:     {total_stats['interactions_skipped']}")
    print(f"Errors:                   {total_stats['errors']}")

    if args.dry_run:
        print(f"\n{'='*80}")
        print("DRY RUN COMPLETE - No files were modified")
        print("Run without --dry-run to perform actual migration")
        print(f"{'='*80}")
        return 0

    # Validate migration
    print(f"\n{'='*80}")
    print("Validating migration...")
    print(f"{'='*80}")
    valid = validate_migration(proteins, cache_dir)

    if not valid:
        print("\n[ERROR] Validation failed! Check errors above.")
        return 1

    print(f"\n{'='*80}")
    print("[OK] VALIDATION PASSED")
    print(f"{'='*80}")

    # Show database stats
    stats = db.get_database_stats()
    print(f"\nNew database statistics:")
    print(f"  Total proteins:         {stats['total_proteins']}")
    print(f"  Unique interactions:    {stats['unique_interactions']}")
    print(f"  Interaction files:      {stats['total_interaction_files']}")

    # Archive old cache if requested
    if args.archive:
        print(f"\n{'='*80}")
        print("Archiving old cache...")
        print(f"{'='*80}")
        if archive_old_cache(cache_dir):
            print("\n[OK] Migration and archival complete!")
        else:
            print("\n[WARNING] Migration complete but archival failed")
            return 1
    else:
        print(f"\n{'='*80}")
        print("[OK] MIGRATION COMPLETE")
        print(f"{'='*80}")
        print("\nOld cache files are still in place.")
        print("Use --archive to archive them after verification.")

    return 0


if __name__ == "__main__":
    exit(main())
