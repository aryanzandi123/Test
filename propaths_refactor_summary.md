# ProPaths Search/Query Refactoring - Change Summary

## Overview

This refactoring separates "Search" (database lookup) from "Query" (research pipeline) functionality, fixes critical bugs, and improves modal UX.

---

## Context & Motivation

### Problems Solved:
1. **Conflated concerns**: `/api/query` handled both DB lookups AND expensive pipeline runs
2. **Interactors not searchable**: Proteins added as interactors had `total_interactions = 0`
3. **Incorrect counting**: `total_interactions` didn't include reverse links (bidirectional)
4. **History used file DB**: Should query PostgreSQL instead
5. **No main protein modal**: Center node couldn't be clicked for details
6. **Inconsistent button styling**: Emojis, stretched buttons, mixed fonts

---

## Changes by File

### 1. **app.py** - Backend API Refactoring

#### A. Created `/api/search` endpoint (NEW)
**Lines:** ~94-120
```python
@app.route('/api/search/<protein>')
def search_protein(protein):
    """Search for a protein in the database (no querying/research)."""
```
**Purpose:** Instant database lookup without running pipeline
**Returns:** `{"status": "found"|"not_found", "interaction_count": N}`

#### B. Refactored `/api/query` 
**Lines:** ~130-132 (removed instant return check)
**Before:** Checked if protein exists → returned immediately if found
**After:** Always runs pipeline (allows finding NEW interactions)
**Reason:** History feature prevents duplicates via `known_interactions` context

#### C. Deprecated `/api/requery`
**Lines:** ~218-226
**Change:** Added deprecation warning, redirects to `/api/query`
**Reason:** `/api/query` now handles both new and existing proteins

#### D. Removed file cache fallbacks
**Lines:** ~769-819 (`get_results`, `get_visualization`)
**Before:** Tried PostgreSQL → fallback to file cache
**After:** PostgreSQL only (removed file reads)
**Reason:** PostgreSQL is source of truth now

---

### 2. **runner.py** - History Feature Fix

**Lines:** ~1206-1248
**Problem:** `pdb.get_all_interactions()` read from file cache (`cache/proteins/`)
**Solution:** Query PostgreSQL with bidirectional lookup:
```python
db_interactions = db.session.query(Interaction).filter(
    (Interaction.protein_a_id == protein_obj.id) |
    (Interaction.protein_b_id == protein_obj.id)
).all()
```
**Result:** History now uses live database data

---

### 3. **utils/db_sync.py** - Bidirectional Counting Fix

**Lines:** 117-141
**Problem:** Only counted direct queries: `total_interactions = len(interactors)`
**Solution:** Count BOTH directions:
```python
main_protein.total_interactions = db.session.query(Interaction).filter(
    (Interaction.protein_a_id == main_protein.id) |
    (Interaction.protein_b_id == main_protein.id)
).count()
```
**Critical:** Also updates PARTNER proteins' counts (lines 117-121)
**Reason:** Canonical ordering (protein_a_id < protein_b_id) means reverse links exist

---

### 4. **static/script.js** - Landing Page Search Flow

**Lines:** 85-212
**New Functions:**
- `searchProtein()` - calls `/api/search`
- `showQueryPrompt()` - displays "not found" message with button
- `startQuery()` - runs pipeline after user confirmation

**Flow:**
1. User enters protein → search DB first
2. If found → instant navigation to visualization
3. If not found → show "Start Research Query" button
4. User clicks → runs pipeline

---

### 5. **visualizer.py** - Major Modal & UX Improvements

#### A. Main Protein Click → Modal (lines 4706, 6834)
**Before:** `.on('click', requeryMainProtein)` - prompted for rounds
**After:** `.on('click', handleNodeClick)` - opens modal
**Result:** Clicking center protein shows ALL interactions in modal

#### B. Modal Footer Refactoring (4 sections)
**Lines:** 5328-5384 (showInteractionModal), 5626-5681 (showAggregatedInteractionsModal)

**Main Protein Footer:**
- Single "Find New Interactions" button (no Expand/Collapse - it's root)

**Interactor Footer:**
- "Expand" button (conditional - if has data)
- "Query" button (always available)
- "Collapse" button (if already expanded)
- Helper text: "Expand uses existing data • Query finds new interactions"

#### C. Button Styling Fixes
**Changes applied to all buttons:**
1. **Removed emojis:** "🔍 Query" → "Query", "↗️ Expand" → "Expand"
2. **Fixed-width:** Removed `flex: 1`, added `padding: 8px 20px`
3. **Left-aligned:** Buttons no longer stretch to fill width
4. **Increased gap:** `8px` → `12px` between buttons
5. **Sans-serif font:** Added `font-family: var(--font-sans)` to all buttons and text

#### D. Modal Body Font (line 1446)
**Added:** `font-family: var(--font-sans)` to `.modal-body` CSS
**Result:** All modal content uses clean Inter font

#### E. Search from Visualizer (lines 5936-6019)
**New Functions:**
- `searchProteinFromVisualizer()` - DB lookup from viz page
- `startQueryFromVisualizer()` - pipeline execution with config
- `handleQueryFromModal()` - called by Query buttons in modals
- `handleExpandFromModal()` - existing data expansion

---

## User Flows

### Flow 1: Search Existing Protein
1. Enter "ATXN3" → calls `/api/search/ATXN3`
2. Found in DB → instant load `/api/visualize/ATXN3`

### Flow 2: Query New Protein
1. Enter "FAKE123" → calls `/api/search/FAKE123`
2. Not found → shows "Start Research Query" button
3. Click button → calls `/api/query` (runs pipeline)
4. Poll `/api/status/FAKE123` until complete
5. Load visualization

### Flow 3: Main Protein Modal
1. Click center protein → opens modal with ALL interactions
2. Grouped: DIRECT | INDIRECT | SHARED
3. Footer: "Find New Interactions" button only
4. Click button → runs query to find NEW interactors

### Flow 4: Interactor Modal
1. Click any interactor → opens modal
2. Footer shows:
   - "Expand" (loads existing data from DB)
   - "Query" (runs pipeline to find NEW interactors)
3. Choose expansion type

---

## Technical Details

### Database Architecture
- **Canonical ordering:** `protein_a_id < protein_b_id` (enforced)
- **Direction transformation:** Flips when reversing order
- **JSONB storage:** Full interaction payload in `data` column
- **Bidirectional queries:** `(protein_a_id = X) OR (protein_b_id = X)`

### Button Styling Specs
- **Padding:** `8px 20px` (vertical × horizontal)
- **Gap:** `12px` between buttons
- **Font:** Inter sans-serif (`var(--font-sans)`)
- **Width:** Auto (natural content width, no stretching)
- **Alignment:** Left-aligned in row

---

## Testing Checklist

✅ Search ATXN3 → instant load
✅ Search VCP (interactor) → instant load  
✅ Search FAKE123 → "not found" + button
✅ Click main protein → modal with all interactions
✅ Click interactor → modal with Expand + Query buttons
✅ Query button triggers pipeline with progress
✅ Expand button loads existing data
✅ Buttons are fixed-width, left-aligned, no emojis
✅ Modal text uses sans-serif font

---

## Migration Notes

### To apply in correct repo:
```bash
cd /path/to/correct/repo
git apply /tmp/propaths_refactor_changes.patch
```

### Verify after applying:
```bash
git status
git diff --stat
```

### Database cleanup needed:
Run queries to fix existing proteins' `total_interactions` counts:
```python
for protein in Protein.query.all():
    protein.total_interactions = db.session.query(Interaction).filter(
        (Interaction.protein_a_id == protein.id) |
        (Interaction.protein_b_id == protein.id)
    ).count()
db.session.commit()
```

---

## Files Modified

1. **app.py** - Backend API endpoints (136 lines changed)
2. **runner.py** - History feature PostgreSQL integration (47 lines changed)
3. **static/script.js** - Landing page search flow (64 lines changed)
4. **utils/db_sync.py** - Bidirectional counting (14 lines changed)
5. **visualizer.py** - Modal refactoring, button styling (328 lines changed)

**Total:** ~589 lines changed across 5 files
