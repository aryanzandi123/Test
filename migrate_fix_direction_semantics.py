"""
Fix direction semantics: Convert query-relative → protein-absolute directions.

PROBLEM:
Current database stores directions as query-context-relative:
- "main_to_primary" (main protein affects primary interactor)
- "primary_to_main" (primary interactor affects main protein)

But canonical ordering (protein_a_id < protein_b_id) means directions need to be
protein-order-absolute for consistent retrieval across different query perspectives.

SOLUTION:
Convert to absolute directions:
- "a_to_b" (protein_a → protein_b, regardless of which was queried)
- "b_to_a" (protein_b → protein_a, regardless of which was queried)
- "bidirectional" (mutual regulation, unchanged)

ALGORITHM:
For each interaction:
1. Get discovered_in_query (which protein originally found this interaction)
2. Determine if discovered protein is protein_a or protein_b
3. Convert query-relative → absolute based on perspective:
   - If protein_a was query: "main_to_primary" → "a_to_b", "primary_to_main" → "b_to_a"
   - If protein_b was query: "main_to_primary" → "b_to_a", "primary_to_main" → "a_to_b"
   - Bidirectional stays bidirectional

Usage:
    python migrate_fix_direction_semantics.py
"""

from app import app, db
from models import Protein, Interaction
import sys
from datetime import datetime


def convert_direction_to_absolute(
    stored_direction: str,
    protein_a_symbol: str,
    protein_b_symbol: str,
    discovered_in_query: str
) -> str:
    """
    Convert query-relative direction to protein-absolute direction.

    Args:
        stored_direction: Current direction ("main_to_primary", "primary_to_main", "bidirectional", etc.)
        protein_a_symbol: Canonical protein_a (lower ID)
        protein_b_symbol: Canonical protein_b (higher ID)
        discovered_in_query: Which protein originally queried this interaction

    Returns:
        Absolute direction: "a_to_b", "b_to_a", or "bidirectional"
    """
    # Handle None, empty, or already-migrated directions
    if not stored_direction:
        return "bidirectional"

    # If already migrated, return as-is
    if stored_direction in ["a_to_b", "b_to_a"]:
        return stored_direction

    # Bidirectional is direction-agnostic
    if stored_direction == "bidirectional":
        return "bidirectional"

    # Determine which protein was the query ("main")
    query_is_protein_a = (discovered_in_query == protein_a_symbol)

    # Convert based on query perspective
    if query_is_protein_a:
        # protein_a was queried
        if stored_direction == "main_to_primary":
            # protein_a (main) → protein_b (primary)
            return "a_to_b"
        elif stored_direction == "primary_to_main":
            # protein_b (primary) → protein_a (main)
            return "b_to_a"
        else:
            # Unknown direction, default to bidirectional
            print(f"  ⚠️  Unknown direction '{stored_direction}', defaulting to bidirectional", file=sys.stderr)
            return "bidirectional"
    else:
        # protein_b was queried
        if stored_direction == "main_to_primary":
            # protein_b (main) → protein_a (primary)
            return "b_to_a"
        elif stored_direction == "primary_to_main":
            # protein_a (primary) → protein_b (main)
            return "a_to_b"
        else:
            # Unknown direction, default to bidirectional
            print(f"  ⚠️  Unknown direction '{stored_direction}', defaulting to bidirectional", file=sys.stderr)
            return "bidirectional"


def migrate_direction_semantics():
    """Convert all interactions from query-relative to protein-absolute directions."""

    with app.app_context():
        print("\n" + "="*60)
        print("[MIGRATION] Fixing direction semantics...")
        print("[MIGRATION] Converting query-relative → protein-absolute")
        print("="*60 + "\n")

        # Get all interactions
        all_interactions = Interaction.query.all()
        total_count = len(all_interactions)

        if total_count == 0:
            print("[MIGRATION] No interactions found in database.")
            print("="*60 + "\n")
            return 0

        print(f"[MIGRATION] Processing {total_count} interactions...\n")

        # Track migration statistics
        stats = {
            "migrated": 0,
            "already_migrated": 0,
            "bidirectional": 0,
            "no_discovered_in": 0,
            "errors": 0
        }

        # Process each interaction
        for idx, interaction in enumerate(all_interactions, 1):
            try:
                protein_a = interaction.protein_a.symbol
                protein_b = interaction.protein_b.symbol
                stored_direction = interaction.direction
                discovered_in = interaction.discovered_in_query

                # Skip if already migrated (direction is already absolute)
                if stored_direction in ["a_to_b", "b_to_a"]:
                    stats["already_migrated"] += 1
                    if idx % 100 == 0:
                        print(f"[{idx}/{total_count}] Already migrated: {protein_a} ↔ {protein_b}")
                    continue

                # Handle missing discovered_in_query (shouldn't happen, but be safe)
                if not discovered_in:
                    print(f"[{idx}/{total_count}] ⚠️  Missing discovered_in_query: {protein_a} ↔ {protein_b}")
                    print(f"  Defaulting to bidirectional")
                    interaction.direction = "bidirectional"
                    stats["no_discovered_in"] += 1
                    continue

                # Convert direction
                old_direction = stored_direction
                new_direction = convert_direction_to_absolute(
                    stored_direction,
                    protein_a,
                    protein_b,
                    discovered_in
                )

                # Update database
                interaction.direction = new_direction
                interaction.updated_at = datetime.utcnow()

                # Update data JSONB for consistency
                if interaction.data:
                    interaction.data["_direction_migrated"] = datetime.utcnow().isoformat()
                    interaction.data["_old_direction"] = old_direction

                # Track stats
                if new_direction == "bidirectional":
                    stats["bidirectional"] += 1
                else:
                    stats["migrated"] += 1

                # Log progress
                if old_direction != new_direction:
                    arrow = "→" if new_direction == "a_to_b" else ("←" if new_direction == "b_to_a" else "↔")
                    print(f"[{idx}/{total_count}] {protein_a} {arrow} {protein_b}")
                    print(f"  Query: {discovered_in}")
                    print(f"  Before: {old_direction} → After: {new_direction}")

                # Show progress every 50 interactions
                if idx % 50 == 0:
                    print(f"\n[PROGRESS] {idx}/{total_count} interactions processed\n")

            except Exception as e:
                print(f"[{idx}/{total_count}] ❌ Error processing {protein_a} ↔ {protein_b}: {e}", file=sys.stderr)
                stats["errors"] += 1
                continue

        # Commit all changes
        try:
            db.session.commit()
            print("\n" + "="*60)
            print("[MIGRATION] ✓ Successfully migrated direction semantics")
            print("="*60)
            print(f"\nStatistics:")
            print(f"  Total interactions:  {total_count}")
            print(f"  Migrated (a_to_b/b_to_a): {stats['migrated']}")
            print(f"  Bidirectional (unchanged): {stats['bidirectional']}")
            print(f"  Already migrated:    {stats['already_migrated']}")
            print(f"  Missing discovered_in: {stats['no_discovered_in']}")
            print(f"  Errors:              {stats['errors']}")
            print("="*60 + "\n")

            return stats["migrated"] + stats["bidirectional"]

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ [MIGRATION] Failed to commit changes: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return -1


if __name__ == "__main__":
    print("\nProPaths Database Migration: Fix Direction Semantics")
    print("=" * 60)
    print("Converting query-relative → protein-absolute directions")
    print("="*60)

    count = migrate_direction_semantics()

    if count > 0:
        print("\n✓ Migration completed successfully!")
        print(f"  Processed {count} interaction(s)")
        print("\nNext steps:")
        print("  1. Update db_sync.py to store absolute directions (new writes)")
        print("  2. Update app.py to convert absolute → query-relative (reads)")
        print("  3. Test visualization with ATXN3 and VCP")
        sys.exit(0)
    elif count == 0:
        print("\n✓ No interactions to migrate (database empty or already migrated)")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. See error above.")
        sys.exit(1)
