"""
Fix corrupted direct interactions that were incorrectly marked as indirect
with self-referential upstream_interactor values.

This script identifies and fixes interactions where:
- interaction_type='indirect'
- upstream_interactor equals one of the proteins in the interaction
- Example: ATXN3↔VCP where upstream_interactor='VCP' (nonsensical)

These occur due to chain processing bug where direct interactions serving
as mediators get overwritten with incorrect chain metadata.

Usage:
    python migrate_fix_indirect_corruption.py
"""

from app import app, db
from models import Protein, Interaction
import sys
from datetime import datetime


def fix_corrupted_interactions():
    """Find and fix all corrupted direct interactions."""

    with app.app_context():
        print("\n" + "="*60)
        print("[MIGRATION] Fixing corrupted indirect interactions...")
        print("="*60 + "\n")

        # Find all interactions with self-referential upstream
        all_interactions = Interaction.query.all()

        corrupted = []
        for interaction in all_interactions:
            upstream = interaction.upstream_interactor
            protein_a = interaction.protein_a.symbol
            protein_b = interaction.protein_b.symbol

            # Check if upstream_interactor is self-referential (corruption indicator)
            if upstream and upstream in [protein_a, protein_b]:
                corrupted.append(interaction)

        print(f"[MIGRATION] Found {len(corrupted)} corrupted interactions\n")

        if len(corrupted) == 0:
            print("[MIGRATION] ✓ No corrupted interactions found. Database is clean!")
            print("="*60 + "\n")
            return 0

        # Fix each corrupted interaction
        for idx, interaction in enumerate(corrupted, 1):
            protein_a = interaction.protein_a.symbol
            protein_b = interaction.protein_b.symbol
            old_type = interaction.interaction_type
            old_upstream = interaction.upstream_interactor

            print(f"[{idx}/{len(corrupted)}] Fixing: {protein_a} ↔ {protein_b}")
            print(f"  Before: type={old_type}, upstream={old_upstream}")

            # Reset to direct (these are always direct interactions corrupted by chain processing)
            interaction.interaction_type = "direct"
            interaction.upstream_interactor = None
            interaction.mediator_chain = None
            interaction.depth = 1
            interaction.updated_at = datetime.utcnow()

            # Also fix data dict to keep consistency
            if interaction.data:
                interaction.data["interaction_type"] = "direct"
                interaction.data["upstream_interactor"] = None
                interaction.data["mediator_chain"] = None
                interaction.data["depth"] = 1
                interaction.data["_migration_fixed"] = datetime.utcnow().isoformat()

            print(f"  After:  type=direct, upstream=None")
            print()

        # Commit all changes
        try:
            db.session.commit()
            print("="*60)
            print(f"[MIGRATION] ✓ Successfully fixed {len(corrupted)} corrupted interactions")
            print("="*60 + "\n")

            # Show summary by protein
            print("Fixed interactions by protein:")
            protein_counts = {}
            for interaction in corrupted:
                for protein in [interaction.protein_a.symbol, interaction.protein_b.symbol]:
                    protein_counts[protein] = protein_counts.get(protein, 0) + 1

            for protein, count in sorted(protein_counts.items(), key=lambda x: -x[1]):
                print(f"  {protein}: {count} interactions")
            print()

            return len(corrupted)

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ [MIGRATION] Failed to commit changes: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return -1


if __name__ == "__main__":
    print("\nProPaths Database Migration: Fix Indirect Corruption")
    print("=" * 60)
    print("This script will fix direct interactions incorrectly marked as indirect.")
    print("="*60)

    count = fix_corrupted_interactions()

    if count > 0:
        print("\n✓ Migration completed successfully!")
        print(f"  Fixed {count} corrupted interaction(s)")
        print("\nNext steps:")
        print("  1. Re-visualize affected proteins (e.g., ATXN3)")
        print("  2. Verify direct arrows now appear correctly")
        print("  3. Check modal titles show correct protein pairs")
        sys.exit(0)
    elif count == 0:
        print("\n✓ No corrupted data found. Database is clean!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. See error above.")
        sys.exit(1)
