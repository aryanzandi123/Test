# DATABASE INTEGRATION GUIDE FOR CLAUDE CODE

## CRITICAL CONTEXT

This guide explains how to integrate code changes from a **file-based protein database** system into a **PostgreSQL-backed system**. The two codebases share the same frontend, pipeline, and features but differ fundamentally in how they store and retrieve protein interaction data.

**Your codebase:** File-based symmetric storage (`cache/proteins/PROTEIN_A/interactions/PROTEIN_B.json`)
**Target codebase:** PostgreSQL database with canonical ordering and SQLAlchemy ORM

---

## TABLE OF CONTENTS

1. [Architectural Differences](#architectural-differences)
2. [The Canonical Ordering Principle](#the-canonical-ordering-principle)
3. [Key Files & Their Equivalents](#key-files--their-equivalents)
4. [Data Flow Comparison](#data-flow-comparison)
5. [Integration Patterns](#integration-patterns)
6. [Code Translation Examples](#code-translation-examples)
7. [Testing & Validation](#testing--validation)
8. [Common Pitfalls](#common-pitfalls)

---

## ARCHITECTURAL DIFFERENCES

### Your System (File-Based Database)

**Storage Layer:**
```
cache/proteins/
  ATXN3/
    metadata.json
    interactions/
      VCP.json          # Forward direction
      HDAC6.json
  VCP/
    metadata.json
    interactions/
      ATXN3.json        # Symmetric copy (reversed direction)
      UFD1L.json
```

**Key Module:** `utils/protein_database.py`

**Core Functions:**
- `get_all_interactions(protein)` - Scans filesystem for interactions
- `save_interaction(protein_a, protein_b, data)` - Writes TWO files (symmetric)
- `_flip_interaction_perspective(data, new_main)` - Reverses direction for symmetric copy
- `build_query_snapshot(protein)` - Assembles JSON from files

**Storage Strategy:** Symmetric dual-write (each interaction stored twice from both perspectives)

---

### Target System (PostgreSQL Database)

**Storage Layer:**
```sql
-- PostgreSQL Tables

proteins (
  id SERIAL PRIMARY KEY,
  symbol VARCHAR(50) UNIQUE,
  query_count INTEGER,
  total_interactions INTEGER,
  ...
)

interactions (
  id SERIAL PRIMARY KEY,
  protein_a_id INTEGER REFERENCES proteins(id),
  protein_b_id INTEGER REFERENCES proteins(id),
  data JSONB,  -- FULL interaction payload
  confidence NUMERIC(3,2),
  direction VARCHAR(20),
  arrow VARCHAR(50),
  CONSTRAINT interaction_unique UNIQUE(protein_a_id, protein_b_id),
  CONSTRAINT protein_a_less_than_b CHECK(protein_a_id < protein_b_id)  -- CANONICAL ORDERING!
)
```

**Key Modules:**
- `models.py` - SQLAlchemy ORM models (Protein, Interaction)
- `utils/db_sync.py` - DatabaseSyncLayer (syncs pipeline output → PostgreSQL)
- `app.py` - Flask app with database helpers (`build_full_json_from_db`, `build_expansion_json_from_db`)

**Core Functions:**
- `build_full_json_from_db(protein)` - Queries PostgreSQL, reconstructs JSON with shared links
- `DatabaseSyncLayer.sync_query_results()` - Saves pipeline results to DB
- `build_expansion_json_from_db(protein, visible_proteins)` - Builds expansion with cross-links

**Storage Strategy:** Canonical ordering (each interaction stored ONCE with protein_a_id < protein_b_id)

---

## THE CANONICAL ORDERING PRINCIPLE

This is the **MOST CRITICAL** difference between the two systems.

### Your System: Symmetric Storage

```python
# When ATXN3 (id=1) interacts with VCP (id=20):

# FILE 1: cache/proteins/ATXN3/interactions/VCP.json
{
  "protein_a": "ATXN3",
  "protein_b": "VCP",
  "primary": "VCP",
  "direction": "bidirectional"
}

# FILE 2: cache/proteins/VCP/interactions/ATXN3.json (FLIPPED!)
{
  "protein_a": "VCP",
  "protein_b": "ATXN3",
  "primary": "ATXN3",
  "direction": "bidirectional"  # Same, because bidirectional
}
```

**Result:** 2 files per interaction (symmetric copies)

---

### Target System: Canonical Ordering

```sql
-- When ATXN3 (id=1) interacts with VCP (id=20):

-- ONLY ONE ROW in database:
INSERT INTO interactions (protein_a_id, protein_b_id, direction, data)
VALUES (1, 20, 'bidirectional', {...});

-- protein_a_id < protein_b_id ENFORCED!
-- The CHECK constraint prevents (20, 1) from ever being inserted
```

**Result:** 1 database row per interaction

---

### Why This Matters for Integration

When translating code, you MUST understand:

1. **Your system queries TWO locations** per interaction (forward + reverse files)
2. **Target system queries ONE location** with bidirectional SQL (protein_a OR protein_b)
3. **Direction flipping logic** is handled differently:
   - Your system: `_flip_interaction_perspective()` when reading symmetric file
   - Target system: Direction transformation when storing reversed proteins (in `db_sync.py`)

---

## KEY FILES & THEIR EQUIVALENTS

### Data Access Layer

| Your System | Target System | Purpose |
|-------------|---------------|---------|
| `utils/protein_database.py` | `app.py` (helpers) + `utils/db_sync.py` | Data storage/retrieval |
| `get_all_interactions()` | `build_full_json_from_db()` | Get all interactions for a protein |
| `save_interaction()` | `DatabaseSyncLayer.sync_query_results()` | Save interaction to storage |
| `build_query_snapshot()` | `build_full_json_from_db()` | Build visualization JSON |
| `_flip_interaction_perspective()` | Direction logic in `build_full_json_from_db()` | Handle perspective reversal |

### Database Schema

| Your System | Target System | Purpose |
|-------------|---------------|---------|
| `metadata.json` | `proteins` table | Protein metadata (query stats) |
| `interactions/*.json` files | `interactions` table | Interaction data |
| File-based symmetry | Canonical ordering constraint | Prevent duplicates |

### API Endpoints

| Endpoint | Your Implementation | Target Implementation |
|----------|---------------------|----------------------|
| `/api/results/<protein>` | `build_query_snapshot()` from files | `build_full_json_from_db()` from PostgreSQL |
| `/api/visualize/<protein>` | File-based snapshot | `create_visualization_from_dict()` with DB snapshot |
| `/api/query` (background job) | File writes in `runner.py` | Dual-write (file + DB sync in `run_full_job()`) |

---

## DATA FLOW COMPARISON

### Query Flow: Your System

```
1. User queries ATXN3
   ↓
2. Pipeline discovers 19 interactions (including VCP)
   ↓
3. runner.py calls protein_database.save_interaction("ATXN3", "VCP", data)
   ↓
4. Writes FILE 1: cache/proteins/ATXN3/interactions/VCP.json
   AND FILE 2: cache/proteins/VCP/interactions/ATXN3.json (flipped direction)
   ↓
5. API serves /api/results/ATXN3 by calling build_query_snapshot("ATXN3")
   ↓
6. Scans cache/proteins/ATXN3/interactions/*.json → returns JSON
```

---

### Query Flow: Target System

```
1. User queries ATXN3
   ↓
2. Pipeline discovers 19 interactions (including VCP)
   ↓
3. runner.py calls DatabaseSyncLayer.sync_query_results("ATXN3", snapshot_json)
   ↓
4. For each interaction (e.g., ATXN3 ↔ VCP):
   a. Get or create Protein(symbol="ATXN3")  → id=1
   b. Get or create Protein(symbol="VCP")    → id=20
   c. Enforce canonical ordering: protein_a_id < protein_b_id
      Since 1 < 20, store as (protein_a_id=1, protein_b_id=20)
   d. Store direction as-is (e.g., "bidirectional")
   e. Store FULL interaction data in `data` JSONB column
   ↓
5. API serves /api/results/ATXN3 by calling build_full_json_from_db("ATXN3")
   ↓
6. Queries PostgreSQL:
   SELECT * FROM interactions WHERE protein_a_id = 1 OR protein_b_id = 1
   ↓
7. For each row:
   - If protein_a_id == 1: Use direction as-is
   - If protein_b_id == 1: FLIP direction (main_to_primary ↔ primary_to_main)
   ↓
8. Returns JSON with interactions array
```

---

## INTEGRATION PATTERNS

### Pattern 1: Translating File-Based Data Reads

**Your code:**
```python
# utils/protein_database.py
def get_all_interactions(protein: str) -> List[Dict[str, Any]]:
    interactions = []
    interactions_dir = PROTEINS_DIR / protein / "interactions"

    # Read forward interactions
    for interaction_file in interactions_dir.glob("*.json"):
        interaction_data = _load_json_safe(interaction_file)
        interactions.append(interaction_data)

    # Read reverse interactions (from other proteins)
    for other_protein_dir in PROTEINS_DIR.iterdir():
        reverse_file = other_protein_dir / "interactions" / f"{protein}.json"
        if reverse_file.exists():
            data = _load_json_safe(reverse_file)
            flipped = _flip_interaction_perspective(data, protein)
            interactions.append(flipped)

    return interactions
```

**Target equivalent:**
```python
# app.py
def build_full_json_from_db(protein_symbol: str) -> dict:
    from models import Protein, Interaction

    # Get protein object
    main_protein = Protein.query.filter_by(symbol=protein_symbol).first()
    if not main_protein:
        return None

    # Query interactions (bidirectional due to canonical ordering)
    db_interactions = db.session.query(Interaction).filter(
        (Interaction.protein_a_id == main_protein.id) |
        (Interaction.protein_b_id == main_protein.id)
    ).all()

    interactions_list = []
    for interaction in db_interactions:
        # Determine partner and perspective
        if interaction.protein_a_id == main_protein.id:
            partner = interaction.protein_b
            needs_flip = False
        else:
            partner = interaction.protein_a
            needs_flip = True  # Stored in reversed order

        # Extract FULL data from JSONB
        interaction_data = interaction.data.copy()

        # Fix direction if stored reversed
        if needs_flip:
            if interaction.direction == "main_to_primary":
                interaction_data["direction"] = "primary_to_main"
            elif interaction.direction == "primary_to_main":
                interaction_data["direction"] = "main_to_primary"
            # bidirectional stays the same
        else:
            interaction_data["direction"] = interaction.direction

        interactions_list.append(interaction_data)

    return {"snapshot_json": {"main": protein_symbol, "interactors": interactions_list}}
```

---

### Pattern 2: Translating File-Based Data Writes

**Your code:**
```python
# utils/protein_database.py
def save_interaction(protein_a: str, protein_b: str, interaction_data: Dict) -> bool:
    # Enrich with metadata
    enriched_data = interaction_data.copy()
    enriched_data["protein_a"] = protein_a
    enriched_data["protein_b"] = protein_b

    # Save forward file
    file_a = PROTEINS_DIR / protein_a / "interactions" / f"{protein_b}.json"
    _save_json_safe(file_a, enriched_data)

    # Create symmetric copy (FLIPPED!)
    symmetric_data = _flip_interaction_perspective(enriched_data, protein_b)
    file_b = PROTEINS_DIR / protein_b / "interactions" / f"{protein_a}.json"
    _save_json_safe(file_b, symmetric_data)

    return True
```

**Target equivalent:**
```python
# utils/db_sync.py (inside DatabaseSyncLayer class)
def _save_interaction(self, protein_a: Protein, protein_b: Protein,
                      data: Dict, discovered_in: str) -> bool:
    original_direction = data.get("direction")

    # CANONICAL ORDERING: Always store with lower ID as protein_a
    if protein_a.id < protein_b.id:
        canonical_a = protein_a
        canonical_b = protein_b
        stored_direction = original_direction  # No flip needed
    else:
        # Swap proteins AND flip direction
        canonical_a = protein_b
        canonical_b = protein_a
        # Flip direction
        if original_direction == "main_to_primary":
            stored_direction = "primary_to_main"
        elif original_direction == "primary_to_main":
            stored_direction = "main_to_primary"
        else:
            stored_direction = original_direction  # bidirectional stays same

    # Store full data in JSONB column
    data_copy = data.copy()
    data_copy["_original_direction"] = original_direction

    # Check if exists
    interaction = Interaction.query.filter_by(
        protein_a_id=canonical_a.id,
        protein_b_id=canonical_b.id
    ).first()

    if interaction:
        # UPDATE existing
        interaction.data = data_copy
        interaction.direction = stored_direction
    else:
        # CREATE new
        interaction = Interaction(
            protein_a_id=canonical_a.id,
            protein_b_id=canonical_b.id,
            data=data_copy,
            direction=stored_direction,
            confidence=data.get("confidence"),
            arrow=data.get("arrow"),
            discovered_in_query=discovered_in
        )
        db.session.add(interaction)

    db.session.flush()
    return True
```

---

### Pattern 3: Integrating New Features

When you add a new feature (e.g., new modal, table view, chat panel), follow this pattern:

**Step 1:** Identify if feature touches data layer

**Step 2:** Map file operations to database operations

| Your Code Pattern | Target Code Pattern |
|-------------------|---------------------|
| `protein_database.get_all_interactions()` | `build_full_json_from_db()` |
| `protein_database.save_interaction()` | `DatabaseSyncLayer.sync_query_results()` |
| `protein_database.build_query_snapshot()` | `build_full_json_from_db()` (same output) |
| File path checks (`if file.exists()`) | Database queries (`if Protein.query.filter_by(...).first()`) |
| JSON file reads | JSONB column access (`interaction.data`) |

**Step 3:** Update API endpoints if needed

**Example: Adding a new `/api/protein_stats` endpoint**

Your implementation:
```python
@app.route('/api/protein_stats/<protein>')
def get_stats(protein):
    metadata = protein_database.get_protein_metadata(protein)
    interactions = protein_database.get_all_interactions(protein)
    return jsonify({
        "query_count": metadata.get("query_count", 0),
        "total_interactions": len(interactions)
    })
```

Target equivalent:
```python
@app.route('/api/protein_stats/<protein>')
def get_stats(protein):
    from models import Protein, Interaction

    # Query protein from database
    protein_obj = Protein.query.filter_by(symbol=protein).first()
    if not protein_obj:
        return jsonify({"error": "Protein not found"}), 404

    # Count interactions (bidirectional query)
    interaction_count = db.session.query(Interaction).filter(
        (Interaction.protein_a_id == protein_obj.id) |
        (Interaction.protein_b_id == protein_obj.id)
    ).count()

    return jsonify({
        "query_count": protein_obj.query_count,
        "total_interactions": interaction_count
    })
```

---

## CODE TRANSLATION EXAMPLES

### Example 1: Shared Interactor Links

This is a NEW feature in the target system that doesn't exist in file-based version.

**Target system feature:**
When querying HDAC6, the system finds that two of its interactors (ATXN3 and VCP) also interact with each other. This creates a "triangle" relationship that's visualized as dashed lines.

**How it works:**
```python
# app.py - build_full_json_from_db()

# After getting direct interactions for HDAC6
interactor_proteins = [...]  # List of Protein objects (ATXN3, VCP, ...)

# Query for interactions BETWEEN the interactors
if len(interactor_proteins) > 1:
    interactor_ids = [p.id for p in interactor_proteins]

    # Find interactions where BOTH endpoints are in the interactor list
    shared_interactions = db.session.query(Interaction).filter(
        Interaction.protein_a_id.in_(interactor_ids),
        Interaction.protein_b_id.in_(interactor_ids)
    ).all()

    # Add to interactions list with "shared" type
    for shared_ix in shared_interactions:
        shared_data = shared_ix.data.copy()
        shared_data["type"] = "shared"
        shared_data["source"] = shared_ix.protein_a.symbol
        shared_data["target"] = shared_ix.protein_b.symbol
        interactions_list.append(shared_data)
```

**To integrate this into your system:**
You would need to add similar logic to `protein_database.py`:
```python
def build_query_snapshot_with_shared_links(protein: str) -> Dict:
    # Get direct interactions
    direct_interactions = get_all_interactions(protein)

    # Get list of partner proteins
    partner_symbols = [i.get("primary") for i in direct_interactions]

    # Find interactions between partners
    shared_interactions = []
    for i, partner_a in enumerate(partner_symbols):
        for partner_b in partner_symbols[i+1:]:
            # Check if partner_a ↔ partner_b interaction exists
            interaction_file = PROTEINS_DIR / partner_a / "interactions" / f"{partner_b}.json"
            if interaction_file.exists():
                data = _load_json_safe(interaction_file)
                if data:
                    data["type"] = "shared"
                    data["source"] = partner_a
                    data["target"] = partner_b
                    shared_interactions.append(data)

    return {
        "snapshot_json": {
            "main": protein,
            "interactors": direct_interactions + shared_interactions
        }
    }
```

---

### Example 2: Cross-Link Discovery (Expansion)

**Target system feature (`build_expansion_json_from_db`):**

When expanding VCP from an HDAC6 graph (where ATXN3 is already visible), the system automatically discovers if any of VCP's NEW interactors also interact with HDAC6 or ATXN3.

```python
# app.py - build_expansion_json_from_db()

def build_expansion_json_from_db(protein_symbol: str, visible_proteins: list = None):
    # Get base expansion (VCP's direct interactions)
    result = build_full_json_from_db(protein_symbol)

    if not visible_proteins:
        return result

    # Get new proteins from expansion
    new_proteins = [p for p in result["snapshot_json"]["proteins"]
                   if p != protein_symbol and p not in visible_proteins]

    # Query for cross-links between new proteins and visible proteins
    new_protein_objs = Protein.query.filter(Protein.symbol.in_(new_proteins)).all()
    visible_protein_objs = Protein.query.filter(Protein.symbol.in_(visible_proteins)).all()

    new_ids = [p.id for p in new_protein_objs]
    visible_ids = [p.id for p in visible_protein_objs]

    # Find interactions where one is new and other is visible
    cross_links = db.session.query(Interaction).filter(
        db.or_(
            db.and_(
                Interaction.protein_a_id.in_(new_ids),
                Interaction.protein_b_id.in_(visible_ids)
            ),
            db.and_(
                Interaction.protein_a_id.in_(visible_ids),
                Interaction.protein_b_id.in_(new_ids)
            )
        )
    ).all()

    # Add cross-links to result
    for cross_ix in cross_links:
        cross_data = cross_ix.data.copy()
        cross_data["type"] = "cross_link"
        cross_data["source"] = cross_ix.protein_a.symbol
        cross_data["target"] = cross_ix.protein_b.symbol
        result["snapshot_json"]["interactions"].append(cross_data)

    return result
```

**File-based equivalent:** Similar to shared links example above, scan filesystem for interactions between new and visible proteins.

---

### Example 3: Flask App Context Requirement

**CRITICAL for background threads in target system:**

The target system uses Flask-SQLAlchemy, which requires an app context when accessing the database from background threads.

**Target code pattern:**
```python
# runner.py - run_full_job()

def run_full_job(user_query, jobs, lock, flask_app=None):
    # ... pipeline runs ...

    # CRITICAL: Wrap database operations in app context
    try:
        from utils.db_sync import DatabaseSyncLayer

        if flask_app is not None:
            with flask_app.app_context():  # <-- REQUIRED!
                sync_layer = DatabaseSyncLayer()
                db_stats = sync_layer.sync_query_results(
                    protein_symbol=user_query,
                    snapshot_json=final_payload.get("snapshot_json"),
                    ctx_json=final_payload.get("ctx_json")
                )
        else:
            print("⚠️ Flask app not provided - skipping DB sync")
    except Exception as e:
        print(f"⚠️ Database sync failed: {e}")
```

**Why this matters:**
- File-based system: No app context needed (direct file I/O)
- Target system: SQLAlchemy sessions are thread-local and require app context

**Integration rule:**
When porting code that runs in background threads and accesses the database, always wrap DB operations in `with flask_app.app_context():`.

---

## TESTING & VALIDATION

### Test 1: Canonical Ordering Verification

Ensure interactions are never duplicated in database:

```python
# Test script
from models import db, Protein, Interaction

# Query for ATXN3 ↔ VCP interaction
atxn3 = Protein.query.filter_by(symbol="ATXN3").first()
vcp = Protein.query.filter_by(symbol="VCP").first()

# Check BOTH orderings
forward = Interaction.query.filter_by(
    protein_a_id=atxn3.id, protein_b_id=vcp.id
).first()

reverse = Interaction.query.filter_by(
    protein_a_id=vcp.id, protein_b_id=atxn3.id
).first()

# ONLY ONE should exist
assert (forward is not None) != (reverse is not None), "Duplicate or missing!"

# Should be stored with lower ID first
if atxn3.id < vcp.id:
    assert forward is not None, "Should be stored as (ATXN3, VCP)"
else:
    assert reverse is not None, "Should be stored as (VCP, ATXN3)"

print("✓ Canonical ordering verified")
```

---

### Test 2: Direction Flipping Correctness

Verify that direction is correctly transformed when querying from different perspectives:

```python
# Test script

# Query ATXN3 → should see VCP with original direction
atxn3_result = build_full_json_from_db("ATXN3")
vcp_interaction = next(i for i in atxn3_result["snapshot_json"]["interactors"]
                       if i["primary"] == "VCP")
atxn3_direction = vcp_interaction["direction"]

# Query VCP → should see ATXN3 with FLIPPED direction
vcp_result = build_full_json_from_db("VCP")
atxn3_interaction = next(i for i in vcp_result["snapshot_json"]["interactors"]
                         if i["primary"] == "ATXN3")
vcp_direction = atxn3_interaction["direction"]

# Verify flipping logic
if atxn3_direction == "main_to_primary":
    assert vcp_direction == "primary_to_main", "Direction not flipped!"
elif atxn3_direction == "primary_to_main":
    assert vcp_direction == "main_to_primary", "Direction not flipped!"
elif atxn3_direction == "bidirectional":
    assert vcp_direction == "bidirectional", "Bidirectional should stay same"

print("✓ Direction flipping correct")
```

---

### Test 3: Shared Link Discovery

Verify that shared links are correctly discovered:

```python
# Query HDAC6 (which has ATXN3 and VCP as interactors)
result = build_full_json_from_db("HDAC6")
interactions = result["snapshot_json"]["interactors"]

# Find shared link (ATXN3 ↔ VCP)
shared_links = [i for i in interactions if i.get("type") == "shared"]

# Should find at least one shared link
assert len(shared_links) > 0, "No shared links found!"

# Verify it connects two interactors (not involving HDAC6)
for shared in shared_links:
    source = shared.get("source")
    target = shared.get("target")
    assert source != "HDAC6", "Shared link should not involve main protein"
    assert target != "HDAC6", "Shared link should not involve main protein"

print(f"✓ Found {len(shared_links)} shared links")
```

---

## COMMON PITFALLS

### Pitfall 1: Assuming Symmetric Files Exist

**Your code:**
```python
# This works in file-based system
vcp_to_atxn3_file = PROTEINS_DIR / "VCP" / "interactions" / "ATXN3.json"
if vcp_to_atxn3_file.exists():
    # Load data...
```

**Target system:**
```python
# Only ONE row exists in database
# Must query bidirectionally:
interaction = Interaction.query.filter(
    ((Interaction.protein_a_id == vcp.id) & (Interaction.protein_b_id == atxn3.id)) |
    ((Interaction.protein_a_id == atxn3.id) & (Interaction.protein_b_id == vcp.id))
).first()
```

**Fix:** Always use bidirectional queries in target system.

---

### Pitfall 2: Forgetting to Flip Direction

**Your code:**
```python
# File-based system stores flipped direction in symmetric file
# So reading is straightforward
data = _load_json_safe(file)
direction = data["direction"]  # Already correct for this perspective
```

**Target system:**
```python
# Database stores direction from ONE perspective
# Must flip when querying from other side
if needs_flip:
    if stored_direction == "main_to_primary":
        actual_direction = "primary_to_main"
    elif stored_direction == "primary_to_main":
        actual_direction = "main_to_primary"
    else:
        actual_direction = stored_direction
```

**Fix:** Always check if direction needs flipping based on query perspective.

---

### Pitfall 3: Not Using App Context in Background Threads

**Your code:**
```python
# File I/O doesn't need app context
def background_job():
    protein_database.save_interaction("A", "B", data)
```

**Target system:**
```python
# Database access REQUIRES app context in threads
def background_job(flask_app):
    with flask_app.app_context():  # <-- REQUIRED!
        sync_layer.sync_query_results(...)
```

**Fix:** Always wrap DB operations in `with flask_app.app_context():` when in background threads.

---

### Pitfall 4: Hardcoding File Paths

**Your code:**
```python
cache_file = f"cache/{protein}.json"
if os.path.exists(cache_file):
    # ...
```

**Target system:**
```python
# Check database first, file cache second
protein_obj = Protein.query.filter_by(symbol=protein).first()
if protein_obj and protein_obj.total_interactions > 0:
    # Build from database
    result = build_full_json_from_db(protein)
else:
    # Fallback to file cache
    cache_file = f"cache/{protein}.json"
    if os.path.exists(cache_file):
        # ...
```

**Fix:** Always check database first, use file cache as fallback.

---

### Pitfall 5: Assuming Data is in Separate Fields

**Your code:**
```python
# File stores data in top-level fields
interaction_data = {
    "primary": "VCP",
    "direction": "bidirectional",
    "evidence": [...],
    "functions": [...]
}
```

**Target system:**
```python
# Database stores EVERYTHING in `data` JSONB column
interaction.data = {
    "primary": "VCP",
    "direction": "bidirectional",
    "evidence": [...],
    "functions": [...],
    "_original_direction": "bidirectional",
    "_query_context": "ATXN3"
}

# Some fields also denormalized for fast queries
interaction.direction = "bidirectional"  # For WHERE clauses
interaction.confidence = 0.94
interaction.arrow = "regulates"
```

**Fix:** Extract from `data` JSONB column, but use denormalized fields for filtering.

---

## INTEGRATION CHECKLIST

When integrating a new feature from your codebase:

- [ ] **Identify all file I/O operations** - Map to database queries
- [ ] **Check for symmetric storage assumptions** - Adapt to canonical ordering
- [ ] **Verify direction handling** - Add flipping logic if needed
- [ ] **Update API endpoints** - Use `build_full_json_from_db()` instead of file reads
- [ ] **Add app context for background threads** - Wrap DB access in `with flask_app.app_context():`
- [ ] **Test bidirectional queries** - Verify interactions appear from both protein perspectives
- [ ] **Preserve backward compatibility** - Keep file cache fallback during transition
- [ ] **Update tests** - Add database-specific test cases
- [ ] **Document changes in CLAUDE.md** - Update the target system's documentation

---

## MIGRATION WORKFLOW

If you need to sync changes between codebases:

### 1. Frontend/UI Changes (Safe - No Database Impact)

**Examples:** New modal, table view, chat panel, CSS changes

**Process:**
1. Copy HTML/CSS/JS changes directly
2. Test in target system
3. No database modifications needed

---

### 2. API Endpoint Changes (Requires Mapping)

**Examples:** New `/api/` route, modified response format

**Process:**
1. Identify data access patterns in your code
2. Replace `protein_database.*` calls with database equivalents
3. Map file operations to SQL queries
4. Test with both database and file cache fallback

**Example:**
```python
# Your code
@app.route('/api/protein/<name>')
def get_protein(name):
    snapshot = protein_database.build_query_snapshot(name)
    return jsonify(snapshot)

# Target equivalent
@app.route('/api/protein/<name>')
def get_protein(name):
    # Try database first
    try:
        result = build_full_json_from_db(name)
        if result:
            return jsonify(result)
    except Exception as e:
        print(f"DB query failed: {e}")

    # Fallback to file cache
    cache_file = os.path.join(CACHE_DIR, f"{name}.json")
    if os.path.exists(cache_file):
        return send_from_directory(CACHE_DIR, f"{name}.json")

    return jsonify({"error": "Not found"}), 404
```

---

### 3. Data Storage Changes (Requires Careful Integration)

**Examples:** New interaction fields, metadata changes

**Process:**
1. Update `models.py` if new database columns needed
2. Create migration script if schema changes
3. Update `utils/db_sync.py` to handle new fields
4. Update file cache writes for backward compatibility
5. Test data integrity

**Example: Adding a new "interaction_type" field**

```python
# 1. Update models.py
class Interaction(db.Model):
    # ... existing fields ...
    interaction_type = db.Column(db.String(50))  # NEW

# 2. Update db_sync.py
def _save_interaction(self, ...):
    interaction = Interaction(
        # ... existing fields ...
        interaction_type=data.get("interaction_type")  # NEW
    )

# 3. Update file cache writes (backward compat)
snapshot_only = {
    "snapshot_json": final_payload.get("snapshot_json", {}),
    "interaction_type": "..."  # NEW
}
```

---

### 4. Pipeline Changes (Moderate Risk)

**Examples:** New processing steps, validation logic

**Process:**
1. Copy pipeline logic from `runner.py`
2. Ensure no file-based assumptions
3. Test with sample proteins
4. Verify database sync still works

---

## FINAL NOTES

### Key Differences Summary

| Aspect | Your System | Target System |
|--------|-------------|---------------|
| **Storage** | Files (symmetric) | PostgreSQL (canonical) |
| **Duplication Prevention** | File checks | UNIQUE constraint + CHECK(a<b) |
| **Direction Handling** | Flipped in symmetric file | Flipped on read if reversed |
| **Query Performance** | Filesystem scan | Indexed SQL queries |
| **Shared Links** | Manual scanning | Database JOIN queries |
| **Concurrency** | File locks | Database transactions |

---

### When in Doubt

1. **Read the target code first** - Don't assume file patterns apply
2. **Test bidirectionally** - Query from both protein perspectives
3. **Check app context** - Background threads need it
4. **Verify direction flipping** - Canonical ordering requires it
5. **Fallback to files** - Maintain backward compatibility

---

### Resources

- **Target codebase CLAUDE.md** - Primary documentation
- **models.py** - Database schema reference
- **utils/db_sync.py** - Canonical ordering implementation
- **app.py** (lines 270-600) - Database query helpers

---

## GLOSSARY

**Canonical Ordering:** Storing each interaction once with `protein_a_id < protein_b_id` to prevent duplicates.

**Symmetric Storage:** Your system's approach of storing each interaction twice (once from each protein's perspective).

**Direction Flipping:** Reversing `main_to_primary` ↔ `primary_to_main` when viewing interaction from opposite perspective.

**Shared Links:** Interactions BETWEEN a protein's interactors (e.g., if HDAC6 interacts with both ATXN3 and VCP, and ATXN3↔VCP also interact, that's a shared link).

**Cross-Links:** During expansion, newly discovered interactions between new proteins and already-visible proteins in the graph.

**JSONB:** PostgreSQL data type for storing JSON with indexing and query support.

**App Context:** Flask-SQLAlchemy requirement for database access in background threads.

---

**Good luck with your integration! This guide should cover 99% of scenarios you'll encounter.**
