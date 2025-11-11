#!/usr/bin/env python3
"""
Database Migration: Deduplicate Interactions

PROBLEM:
- Database currently has duplicate interactions stored in both directions
- Example: (ATXN3→BECN1) AND (BECN1→ATXN3) both exist
- This causes duplicate arrows in frontend visualization

SOLUTION:
- Enforce canonical ordering: protein_a_id < protein_b_id
- Merge duplicates, keeping the richer data
- Update direction fields to match new perspective

SAFETY:
- Dry-run mode by default (preview changes without committing)
- Backup recommended before running with --apply
- Transaction-based (all-or-nothing)
"""

import sys
from datetime import datetime
from typing import Dict, List, Tuple

from app import app
from models import db, Protein, Interaction


def find_duplicate_pairs() -> List[Tuple[Interaction, Interaction]]:
    """
    Find all duplicate interaction pairs.

    Returns:
        List of (interaction1, interaction2) tuples where both represent
        the same protein pair but stored in different directions.
    """
    duplicates = []

    # Get all interactions
    all_interactions = Interaction.query.all()

    # Build map of (sorted_protein_ids) -> [interactions]
    pair_map: Dict[Tuple[int, int], List[Interaction]] = {}

    for interaction in all_interactions:
        # Create canonical key (lower id first)
        key = tuple(sorted([interaction.protein_a_id, interaction.protein_b_id]))

        if key not in pair_map:
            pair_map[key] = []
        pair_map[key].append(interaction)

    # Find pairs with multiple entries
    for key, interactions in pair_map.items():
        if len(interactions) > 1:
            # Found duplicates
            duplicates.append(tuple(interactions))

    return duplicates


def merge_interaction_data(ix1: Interaction, ix2: Interaction) -> dict:
    """
    Merge two interaction data objects, keeping richer data.

    Strategy:
    - Compare evidence counts
    - Keep interaction with more evidence
    - Preserve metadata from both
    """
    data1 = ix1.data or {}
    data2 = ix2.data or {}

    evidence1 = data1.get("evidence", [])
    evidence2 = data2.get("evidence", [])

    if len(evidence1) >= len(evidence2):
        # Keep data1 as base
        merged = data1.copy()
        merged["_merged_from"] = {
            "discovered_in": [ix1.discovered_in_query, ix2.discovered_in_query],
            "created_at": [ix1.created_at.isoformat(), ix2.created_at.isoformat()],
            "migration_date": datetime.utcnow().isoformat()
        }
        return merged
    else:
        # Keep data2 as base
        merged = data2.copy()
        merged["_merged_from"] = {
            "discovered_in": [ix1.discovered_in_query, ix2.discovered_in_query],
            "created_at": [ix1.created_at.isoformat(), ix2.created_at.isoformat()],
            "migration_date": datetime.utcnow().isoformat()
        }
        return merged


def deduplicate_interactions(dry_run: bool = True) -> Dict[str, int]:
    """
    Deduplicate interactions using canonical ordering.

    Args:
        dry_run: If True, preview changes without committing

    Returns:
        Stats dict with counts
    """
    stats = {
        "total_interactions": 0,
        "duplicate_pairs_found": 0,
        "interactions_kept": 0,
        "interactions_deleted": 0,
        "interactions_updated": 0
    }

    with app.app_context():
        stats["total_interactions"] = Interaction.query.count()

        # Find duplicates
        duplicate_pairs = find_duplicate_pairs()
        stats["duplicate_pairs_found"] = len(duplicate_pairs)

        print(f"Found {len(duplicate_pairs)} duplicate interaction pairs")

        if not duplicate_pairs:
            print("✓ No duplicates found! Database is clean.")
            return stats

        # Process each duplicate pair
        for idx, pair in enumerate(duplicate_pairs):
            ix1, ix2 = pair

            # Get protein symbols for logging
            p1_symbol = ix1.protein_a.symbol
            p2_symbol = ix1.protein_b.symbol
            p3_symbol = ix2.protein_a.symbol
            p4_symbol = ix2.protein_b.symbol

            print(f"\n--- Duplicate #{idx + 1} ---")
            print(f"  Interaction 1: {p1_symbol} (id={ix1.protein_a_id}) ↔ {p2_symbol} (id={ix1.protein_b_id})")
            print(f"                 direction={ix1.direction}, discovered_in={ix1.discovered_in_query}")
            print(f"                 evidence_count={len(ix1.data.get('evidence', []))}")
            print(f"  Interaction 2: {p3_symbol} (id={ix2.protein_a_id}) ↔ {p4_symbol} (id={ix2.protein_b_id})")
            print(f"                 direction={ix2.direction}, discovered_in={ix2.discovered_in_query}")
            print(f"                 evidence_count={len(ix2.data.get('evidence', []))}")

            # Determine canonical ordering (lower id as protein_a)
            all_ids = sorted([ix1.protein_a_id, ix1.protein_b_id])
            canonical_a_id = all_ids[0]
            canonical_b_id = all_ids[1]

            # Find which interaction has canonical ordering
            if ix1.protein_a_id == canonical_a_id:
                keep_ix = ix1
                delete_ix = ix2
            else:
                keep_ix = ix2
                delete_ix = ix1

            print(f"  → Keeping: {keep_ix.protein_a.symbol}→{keep_ix.protein_b.symbol} (canonical order)")
            print(f"  → Deleting: {delete_ix.protein_a.symbol}→{delete_ix.protein_b.symbol}")

            # Merge data
            merged_data = merge_interaction_data(ix1, ix2)

            if not dry_run:
                try:
                    # Update kept interaction with merged data
                    keep_ix.data = merged_data
                    keep_ix.updated_at = datetime.utcnow()

                    # Delete duplicate
                    db.session.delete(delete_ix)

                    stats["interactions_kept"] += 1
                    stats["interactions_deleted"] += 1
                    stats["interactions_updated"] += 1

                    print(f"  ✓ Merged and deleted duplicate")

                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    db.session.rollback()
                    raise
            else:
                print(f"  [DRY RUN] Would merge and delete")

        if not dry_run:
            db.session.commit()
            print(f"\n✓ Successfully deduplicated {stats['interactions_deleted']} interactions")
        else:
            print(f"\n[DRY RUN] No changes committed. Run with --apply to execute.")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Deduplicate protein interactions in database")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.apply

    print("=" * 60)
    print("DATABASE DEDUPLICATION MIGRATION")
    print("=" * 60)
    print()

    if dry_run:
        print("MODE: DRY RUN (preview only)")
        print("Run with --apply to actually make changes")
    else:
        print("MODE: APPLY (will modify database)")
        print("⚠️  WARNING: Make sure you have a backup!")
        response = input("\nContinue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    print()

    stats = deduplicate_interactions(dry_run=dry_run)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total interactions (before):  {stats['total_interactions']}")
    print(f"Duplicate pairs found:        {stats['duplicate_pairs_found']}")
    print(f"Interactions kept:            {stats['interactions_kept']}")
    print(f"Interactions deleted:         {stats['interactions_deleted']}")
    print(f"Interactions updated:         {stats['interactions_updated']}")
    print(f"Total interactions (after):   {stats['total_interactions'] - stats['interactions_deleted']}")
    print()


if __name__ == "__main__":
    main()
