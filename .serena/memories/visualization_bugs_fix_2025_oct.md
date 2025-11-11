# ProPaths Visualization Bugs - Fix in Progress (Oct 2025)

## CURRENT STATUS: Ready to implement major visualization fixes

### COMPLETED WORK

1. ✅ **Fixed claim_fact_checker.py** - Changed paper validation from abstract-only to full-paper scope
   - Both protein names can be ANYWHERE in paper (title/abstract/full text)
   - Function details use scientific inference for cascade steps
   - Changed from strict "FALSE if detail wrong" to "REFINE details using canonical pathway knowledge"
   
2. ✅ **Created database migration scripts**
   - `migrate_add_interaction_columns.py` - Adds 5 missing columns + 2 indexes:
     - interaction_type (VARCHAR(20))
     - upstream_interactor (VARCHAR(50))
     - mediator_chain (JSONB)
     - depth (INTEGER DEFAULT 1 NOT NULL)
     - chain_context (JSONB)
     - idx_interactions_depth, idx_interactions_interaction_type
   - `sync_cache_to_db.py` - Syncs existing cache to database without re-querying
   - Both scripts use DATABASE_PUBLIC_URL for local dev

3. ✅ **Verified automatic database sync** - Every query automatically syncs to PostgreSQL

---

## CRITICAL BUGS IDENTIFIED (Need Fixing)

### BUG 1: Indirect Interactors Positioned Wrong ❌

**Problem:** All interactors (direct AND indirect) placed in same ring around main protein. Should use hybrid layout.

**Root Cause:** `visualizer.py` line 4018-4034 (buildInitialGraph)
- Treats all interactors identically
- Doesn't check `interaction_type` field
- No depth-based positioning

**User Requirement:** Hybrid approach
- Direct interactors in inner ring
- Indirect interactors in outer ring (radially separated by depth)
- BUT also clustered near their parent interactor
- Use force simulation to maintain parent proximity

**Files to modify:**
- visualizer.py:
  - buildInitialGraph() (~line 3936)
  - mergeSubgraph() (~line 5789)
  - calculateOrbitalPosition() (~line 4279)
  - createSimulation() (~line 4467)

---

### BUG 2: 60% Have NO FUNCTIONS ❌

**Problem:** Indirect interactions have NO functions field in the data

**Evidence from cache/p62.json:**
- Direct interactions: Have `functions` array with 1-5 functions ✓
- Indirect interactions (NF-κB, NRF2, Atg5, Atg7, Beclin-1, mTORC1): NO functions field ✗

**User Requirement:** Generate functions in pipeline with FULL CHAIN CONTEXT
- Example: p62→TRAF6→NF-κB chain functions should describe the entire cascade
- NOT just TRAF6→NF-κB direct interaction
- Context: "What is the functional significance of [Query]→[Parent]→[Indirect] chain?"

**Files to modify:**
- pipeline/config_gemini_MAXIMIZED.py (or config_dynamic.py)
  - Add new function generation step for indirect interactions
  - Prompt must include full chain context
- runner.py
  - After generating indirect interactions, generate their functions
  - Pass chain context to function generation LLM

---

### BUG 3: Shared Link Functions Wrong ❌

**Problem:** Shared/cross-link interactions show placeholder "do not have context-specific functions"

**Example:** NF-κB ↔ TRAF6 shared link

**User Requirement:** Show actual functions from database
- If shared link is actually an indirect interaction of query → show chain functions
- Otherwise → query database for direct interaction between those two proteins and show their functions

**Files to modify:**
- app.py - build_full_json_from_db() 
  - When building shared links, check if it's indirect of current query
  - If not, query database: `SELECT data FROM interactions WHERE (protein_a=A AND protein_b=B)`
  - Extract functions from data.functions and add to shared link

---

### BUG 4: Function Duplication ❌

**Problem:** Some function boxes show same function repeated 3 times

**Likely Cause:** Deduplication issue in data or frontend rendering

**Quick Fix:** Add deduplication in function box rendering (visualizer.py ~line 5100-5200)

---

## APPROVED IMPLEMENTATION PLAN

### Phase 1: Frontend Fixes (visualizer.py) 🔴 START HERE

1. **Hybrid node positioning**
   - Calculate depth from interaction_type/upstream_interactor
   - Position in depth-based orbital rings
   - Use force simulation to cluster near parent
   - Update collision radii by depth

2. **Remove placeholder messages**
   - Delete "Indirect interactions have limited functional annotation" message
   - Delete "Shared interactions do not have context-specific functions" message
   - Display actual functions from data (if present)

3. **Force simulation depth-aware**
   - Different collision radii: depth 0 (main) > depth 1 (direct) > depth 2+ (indirect)
   - Link forces: longer distance for indirect links
   - Radial force to maintain depth separation

**Locations in visualizer.py:**
- Line 3936: buildInitialGraph()
- Line 4018-4034: Interactor node creation
- Line 4279-4330: calculateOrbitalPosition()
- Line 4467-4490: createSimulation()
- Line 5124-5137: Function modal placeholder messages

---

### Phase 2: Backend - Indirect Function Generation (pipeline) 🟡 AFTER PHASE 1

**New pipeline step:**
1. After indirect interactions generated
2. For each indirect interaction:
   - Identify chain: Query → Parent → Indirect
   - Generate 1-3 functions describing chain significance
   - LLM prompt: "What is the functional significance of the [Query]→[Parent]→[Indirect] interaction chain?"
   - Example: "p62→TRAF6→NF-κB: How does p62 affect NF-κB through TRAF6?"

**Files:**
- pipeline/config_gemini_MAXIMIZED.py - Add function generation step
- runner.py - Call function generation for indirect interactions

**Expected result:** Indirect interactions in cache have `functions` array

---

### Phase 3: Backend - Shared Link Functions (app.py) 🟢 AFTER PHASE 2

**Logic:**
```python
for shared_link in shared_links:
    if shared_link.is_indirect_of_query:
        # Use chain context functions
        shared_link.functions = get_chain_functions(query, parent, shared_link)
    else:
        # Query database for direct interaction
        db_interaction = query_interaction(proteinA, proteinB)
        shared_link.functions = db_interaction.data.functions
```

**Files:**
- app.py - build_full_json_from_db()
- Possibly utils/db_sync.py for helper functions

---

## DATABASE MIGRATION STATUS

**CRITICAL:** User MUST run migration before visualization works!

```bash
# Step 1: Add DATABASE_PUBLIC_URL to .env
DATABASE_PUBLIC_URL=postgresql://postgres:xxx@xxx.proxy.rlwy.net:12345/railway

# Step 2: Run migration
python migrate_add_interaction_columns.py

# Step 3: Sync existing data
python sync_cache_to_db.py --all
```

**Current error:** `column interactions.mediator_chain does not exist`
This blocks ALL database visualization. Migration adds missing columns.

---

## CODE INVESTIGATION FINDINGS

### Indirect Interaction Data Structure (from p62.json)

**Direct interaction example (WITH functions):**
```json
{
  "primary": "KEAP1",
  "direction": "bidirectional",
  "arrow": "inhibits",
  "confidence": 0.9,
  "functions": [
    {
      "function": "NRF2-Dependent Antioxidant Response",
      "arrow": "inhibits",
      "cellular_process": "p62 competes with KEAP1...",
      ...
    }
  ]
}
```

**Indirect interaction example (NO functions):**
```json
{
  "primary": "NF-κB",
  "interaction_type": "indirect",
  "upstream_interactor": "TRAF6",
  "support_summary": "p62 acts as a scaffold protein...",
  "arrow": "binds",
  "mechanism": "Molecular mechanism not fully characterized",
  "evidence": []
  // ❌ NO "functions" FIELD!
}
```

### Positioning Logic (visualizer.py)

**Current (wrong):**
```javascript
// Line 4018-4034
const interactorProteins = proteins.filter(p => p !== SNAP.main);
interactorProteins.forEach((protein, i) => {
  const angle = (2*Math.PI*i)/Math.max(1, interactorProteins.length) - Math.PI/2;
  const x = width/2 + Math.cos(angle)*interactorR;  // Same radius for ALL
  const y = height/2 + Math.sin(angle)*interactorR;
  // All nodes marked as 'interactor' type
});
```

**Needed (hybrid):**
```javascript
// Separate direct and indirect
const directInteractors = proteins.filter(p => isDirectInteractor(p));
const indirectInteractors = proteins.filter(p => isIndirectInteractor(p));

// Position direct in inner ring
directInteractors.forEach(...position at radius R1...);

// Position indirect in outer ring BUT near parent
indirectInteractors.forEach(protein => {
  const parent = findParent(protein);  // upstream_interactor
  const parentPos = getNodePosition(parent);
  // Position near parent but at greater radius
});
```

---

## NEXT STEPS FOR NEW CLAUDE

1. **Read this memory** to understand current state
2. **Ask user preference** on implementation order (Phase 1, 2, or 3 first)
3. **Start with Phase 1** (most visible impact):
   - Fix hybrid positioning in visualizer.py
   - Remove placeholder messages
   - Update force simulation
4. **Test** with existing p62 data (even without functions, positioning should improve)
5. **Then proceed to Phase 2** (backend function generation)

---

## KEY FILES REFERENCE

- **visualizer.py** - Frontend D3.js visualization (embedded in Python HTML generator)
- **pipeline/config_gemini_MAXIMIZED.py** - Pipeline configuration with LLM prompts
- **runner.py** - Pipeline execution engine
- **app.py** - Flask routes, database queries
- **models.py** - SQLAlchemy ORM (Protein, Interaction tables)
- **utils/db_sync.py** - Database sync layer
- **utils/claim_fact_checker.py** - Recently fixed for paper validation
- **cache/p62.json** - Test data showing direct vs indirect structure

---

## ESTIMATED EFFORT

- Phase 1 (Frontend): 2-3 hours (200-300 lines modified in visualizer.py)
- Phase 2 (Backend functions): 2-3 hours (100-200 lines across pipeline files)
- Phase 3 (Shared link functions): 1-2 hours (50-100 lines in app.py)

**Total:** 5-8 hours of careful development + testing

---

## CONTEXT PRESERVED

This memory written: October 28, 2025
Token usage at handoff: ~125k/200k tokens
Ready for new Claude to continue implementation.