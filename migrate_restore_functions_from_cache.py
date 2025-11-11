"""
Restore missing functions from cache files to PostgreSQL database.

PROBLEM:
Many interactions in the database are missing function boxes because:
1. Functions were lost during database updates (didn't merge, only replaced)
2. Previous bug in db_sync.py that ignored new functions when evidence count was equal/less

SOLUTION:
For each interaction missing functions:
1. Look up the corresponding cache file (cache/<PROTEIN>.json)
2. Find the matching interactor in the cache
3. Restore functions array from cache to database

This is safe because:
- Cache files are the SOURCE OF TRUTH (direct pipeline output)
- Database should be a faithful copy of cache

Usage:
    python migrate_restore_functions_from_cache.py
"""

from app import app, db
from models import Protein, Interaction
import sys
import json
from pathlib import Path
from datetime import datetime


def find_interactor_in_cache(cache_data: dict, target_protein: str) -> dict:
    """
    Find interactor in cache data by protein symbol.

    Args:
        cache_data: Parsed cache JSON
        target_protein: Protein symbol to find (e.g., "VCP")

    Returns:
        Interactor dict with functions, or None if not found
    """
    # Handle both formats: {"snapshot_json": {...}} and direct {...}
    snapshot = cache_data.get("snapshot_json", cache_data)

    interactors = snapshot.get("interactors", [])
    for interactor in interactors:
        if interactor.get("primary") == target_protein:
            return interactor

    return None


def restore_functions_from_cache():
    """Restore missing functions from cache files to database."""

    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("❌ Cache directory not found", file=sys.stderr)
        return -1

    with app.app_context():
        print("\n" + "="*60)
        print("[MIGRATION] Restoring missing functions from cache...")
        print("="*60 + "\n")

        # Get all interactions
        all_interactions = Interaction.query.all()
        total_count = len(all_interactions)

        if total_count == 0:
            print("[MIGRATION] No interactions found in database.")
            print("="*60 + "\n")
            return 0

        print(f"[MIGRATION] Scanning {total_count} interactions...\n")

        # Track statistics
        stats = {
            "total": total_count,
            "missing_functions": 0,
            "restored": 0,
            "cache_not_found": 0,
            "interactor_not_found": 0,
            "no_functions_in_cache": 0,
            "errors": 0
        }

        # Process each interaction
        for idx, interaction in enumerate(all_interactions, 1):
            try:
                protein_a = interaction.protein_a.symbol
                protein_b = interaction.protein_b.symbol
                discovered_in = interaction.discovered_in_query

                # Get current functions
                current_functions = interaction.data.get("functions", [])

                # Skip if already has functions
                if current_functions and len(current_functions) > 0:
                    continue

                stats["missing_functions"] += 1

                # Determine which protein is the interactor (not the query)
                if discovered_in == protein_a:
                    query_protein = protein_a
                    interactor_protein = protein_b
                elif discovered_in == protein_b:
                    query_protein = protein_b
                    interactor_protein = protein_a
                else:
                    # Unknown query context, try both
                    print(f"[{idx}/{total_count}] ⚠️  Unknown query context: {protein_a} ↔ {protein_b} (discovered_in={discovered_in})")
                    # Try protein_a as query first
                    query_protein = protein_a
                    interactor_protein = protein_b

                # Look up cache file
                cache_path = cache_dir / f"{query_protein}.json"
                if not cache_path.exists():
                    stats["cache_not_found"] += 1
                    if idx % 50 == 0:
                        print(f"[{idx}/{total_count}] Cache not found: {query_protein}.json")
                    continue

                # Parse cache file
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                except Exception as e:
                    print(f"[{idx}/{total_count}] ❌ Error reading cache {cache_path}: {e}", file=sys.stderr)
                    stats["errors"] += 1
                    continue

                # Find interactor in cache
                interactor_data = find_interactor_in_cache(cache_data, interactor_protein)
                if not interactor_data:
                    stats["interactor_not_found"] += 1
                    continue

                # Extract functions from cache
                cache_functions = interactor_data.get("functions", [])
                if not cache_functions or len(cache_functions) == 0:
                    stats["no_functions_in_cache"] += 1
                    continue

                # Restore functions to database
                print(f"[{idx}/{total_count}] Restoring: {protein_a} ↔ {protein_b}")
                print(f"  Query: {query_protein} → Interactor: {interactor_protein}")
                print(f"  Restoring {len(cache_functions)} function(s)")

                # Update data JSONB
                interaction.data["functions"] = cache_functions
                interaction.data["_functions_restored"] = datetime.utcnow().isoformat()
                interaction.data["_restored_from_cache"] = f"{query_protein}.json"
                interaction.updated_at = datetime.utcnow()

                stats["restored"] += 1

                # Log first few function names
                fn_names = [fn.get("function", "?") for fn in cache_functions[:3]]
                print(f"  Functions: {', '.join(fn_names)}{' ...' if len(cache_functions) > 3 else ''}")
                print()

            except Exception as e:
                print(f"[{idx}/{total_count}] ❌ Error processing {protein_a} ↔ {protein_b}: {e}", file=sys.stderr)
                stats["errors"] += 1
                import traceback
                traceback.print_exc(file=sys.stderr)
                continue

        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "="*60)
            print("[MIGRATION] ✓ Successfully restored functions from cache")
            print("="*60)
            print(f"\nStatistics:")
            print(f"  Total interactions:         {stats['total']}")
            print(f"  Missing functions:          {stats['missing_functions']}")
            print(f"  ✓ Restored:                 {stats['restored']}")
            print(f"  Cache file not found:       {stats['cache_not_found']}")
            print(f"  Interactor not in cache:    {stats['interactor_not_found']}")
            print(f"  No functions in cache:      {stats['no_functions_in_cache']}")
            print(f"  Errors:                     {stats['errors']}")
            print("="*60 + "\n")

            return stats["restored"]

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ [MIGRATION] Failed to commit changes: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return -1


if __name__ == "__main__":
    print("\nProPaths Database Migration: Restore Functions from Cache")
    print("=" * 60)
    print("This script restores missing function boxes from cache files.")
    print("="*60)

    count = restore_functions_from_cache()

    if count > 0:
        print("\n✓ Migration completed successfully!")
        print(f"  Restored functions for {count} interaction(s)")
        print("\nNext steps:")
        print("  1. Re-visualize proteins (e.g., ATXN3)")
        print("  2. Verify all interactors now have function boxes")
        print("  3. Check that functions render with correct labels")
        sys.exit(0)
    elif count == 0:
        print("\n✓ No functions to restore (all interactions have functions or no cache available)")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. See error above.")
        sys.exit(1)
