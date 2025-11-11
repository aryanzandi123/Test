# ProPaths Deployment Guide

**Version:** 1.0 (January 2025)
**System:** Flask + PostgreSQL PPI Visualizer
**Target Platform:** Railway.app

---

## Table of Contents

1. [Railway Production Deployment](#railway-production-deployment)
2. [Database Migration Procedures](#database-migration-procedures)
3. [Post-Deployment Verification](#post-deployment-verification)
4. [Troubleshooting Guide](#troubleshooting-guide)

---

## Railway Production Deployment

### Prerequisites

- Railway.app account with payment method (for PostgreSQL addon)
- GitHub repository with latest code
- Google API key (for LLM-assisted pruning, optional)
- Local PostgreSQL client (for migration testing)

### Step 1: Railway Project Setup

1. **Create New Project**
   ```bash
   # Log in to Railway CLI (optional, can use web UI)
   railway login

   # Link to existing project or create new
   railway init
   ```

2. **Connect GitHub Repository**
   - Go to Railway dashboard
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your ProPaths repository
   - Railway will auto-detect Flask app

3. **Add PostgreSQL Database**
   - In Railway dashboard, click "+ New"
   - Select "Database" → "Add PostgreSQL"
   - Railway provisions database and sets `DATABASE_URL` automatically
   - **Note:** This is the internal URL; external access uses `DATABASE_PUBLIC_URL`

### Step 2: Environment Variables

Configure the following in Railway dashboard (Settings → Variables):

```bash
# Database (automatically set by Railway)
DATABASE_URL=postgresql://postgres:password@hostname:5432/railway

# External database access (for local dev/migrations)
DATABASE_PUBLIC_URL=postgresql://postgres:password@external-hostname:5432/railway

# Optional: LLM features
GOOGLE_API_KEY=your_api_key_here

# Flask configuration
FLASK_ENV=production
FLASK_DEBUG=0

# Security (auto-generated or custom)
SECRET_KEY=your_secret_key_here
```

**Important:** Railway automatically provides `DATABASE_URL` when you add PostgreSQL. Use `DATABASE_PUBLIC_URL` for external connections during migrations.

### Step 3: Build Configuration

Create `railway.toml` in project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python app.py"
healthcheckPath = "/"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### Step 4: Deploy

```bash
# Push to GitHub (Railway auto-deploys)
git push origin main

# Or deploy via CLI
railway up

# Monitor deployment
railway logs
```

### Step 5: Domain Configuration

1. **Railway Subdomain (automatic)**
   - Railway provides: `propaths.up.railway.app`
   - SSL certificate auto-provisioned

2. **Custom Domain (optional)**
   - Go to Settings → Domains
   - Add custom domain (e.g., `propaths.yourdomain.com`)
   - Add CNAME record in DNS:
     ```
     CNAME propaths -> propaths.up.railway.app
     ```
   - SSL provisioned automatically via Let's Encrypt

### Step 6: Monitoring & Logs

```bash
# View real-time logs
railway logs --follow

# View metrics in Railway dashboard
# CPU, Memory, Network, Response times

# Set up alerts (optional)
# Railway → Settings → Notifications
```

---

## Database Migration Procedures

### Overview

ProPaths uses a dual-layer data storage system:
- **Primary:** PostgreSQL database (canonical source)
- **Fallback:** File cache (`cache/<PROTEIN>.json`)

**Migration Philosophy:** Zero-downtime, backward-compatible, gradual rollout.

### Pre-Migration Checklist

- [ ] Database backup completed
- [ ] Migration scripts tested locally
- [ ] Rollback SQL scripts prepared
- [ ] Railway logs accessible
- [ ] Maintenance window scheduled (optional, low-traffic period)

---

## ⚡ MIGRATION EXECUTION ORDER (Quick Reference)

**IMPORTANT:** Migrations must be run in the correct order!

### **Step-by-Step Execution**

```bash
cd "C:\Users\aryan\Documents\Kazie\ProPaths - Copy (5)"

# STEP 1: Run Migration 1 (function_context column)
python migrate_add_function_context.py

# STEP 2: Run Migration 2 (arrows JSONB column)
python migrate_add_arrows.py

# STEP 3: Verify both migrations succeeded
railway run python -c "
from app import app, db
from sqlalchemy import inspect
with app.app_context():
    inspector = inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('interactions')]
    assert 'function_context' in columns, '❌ Missing function_context'
    assert 'arrows' in columns, '❌ Missing arrows'
    print('✅ All migrations applied successfully!')
    print(f'Columns: {columns}')
"

# STEP 4: Deploy new code (optional, if you have pending changes)
git add .
git commit -m "feat: add multi-arrow support and context-aware functions"
git push origin main
```

### **Migration Details**

| # | Script | Adds Column | Purpose | Issue |
|---|--------|-------------|---------|-------|
| 1 | `migrate_add_function_context.py` | `function_context` (VARCHAR) | Context-aware function display | #3 |
| 2 | `migrate_add_arrows.py` | `arrows` (JSONB) | Multi-arrow interactions | #4 |

**Order matters?** Not strictly (both are additive), but run 1→2 for consistency.

**Can I run them multiple times?** Yes! Scripts check if columns exist and skip if already added.

**What about `migrate_to_postgres.py`?** ⚠️ **DO NOT RUN** if database already populated. This is a one-time initial import script (file cache → PostgreSQL).

### **Expected Timeline**

- Migration 1: ~10-30 seconds (depends on # of interactions)
- Migration 2: ~10-30 seconds
- Verification: ~5 seconds
- **Total:** < 2 minutes

### **After Migrations**

**New queries will automatically use new features:**
- ✅ Functions grouped by arrow type (INHIBITS, ACTIVATES, COMPLEX)
- ✅ Context badges (DIRECT PAIR, CHAIN CONTEXT)
- ✅ Multi-arrow display in INTERACTION TYPE section
- ✅ Function name cleanup (removes "Suppression", "Activation", etc.)

**Old proteins remain unchanged** (backward compatible).

**To update old proteins:** Re-query them:
```bash
curl -X POST http://localhost:5000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"protein":"VCP"}'
```

---

### Migration 1: Add Function Context Column

**Purpose:** Support context-aware function display (Issue #3)

**File:** `migrate_add_function_context.py`

#### 1.1 Backup Database

```bash
# Connect to Railway PostgreSQL
railway connect PostgreSQL

# Or use external URL
psql $DATABASE_PUBLIC_URL

# Create backup
pg_dump -h hostname -U postgres -d railway > backup_pre_function_context.sql

# Verify backup
ls -lh backup_pre_function_context.sql
```

#### 1.2 Test Migration Locally (Recommended)

```bash
# Clone production data to local test database
psql -h localhost -U postgres -d test_propaths < backup_pre_function_context.sql

# Run migration on test database
DATABASE_URL=postgresql://localhost/test_propaths python migrate_add_function_context.py

# Verify schema change
psql -h localhost -U postgres -d test_propaths -c "\d interactions"
# Should show: function_context | character varying(20)
```

#### 1.3 Run Production Migration

```bash
# SSH into Railway or run locally with production DATABASE_PUBLIC_URL
railway run python migrate_add_function_context.py
```

**Expected Output:**
```
Migration: Add function_context column
Connecting to database...
Adding function_context column...
✓ Column added successfully
Analyzing existing interactions...
✓ Updated 1,234 interactions with context metadata
Migration complete!
```

#### 1.4 Verify Migration

```sql
-- Check column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'interactions'
  AND column_name = 'function_context';

-- Sample data check
SELECT protein_a_id, protein_b_id, function_context,
       jsonb_array_length(data->'functions') as func_count
FROM interactions
LIMIT 10;
```

#### 1.5 Rollback (if needed)

```sql
-- Remove column (destructive, use only if migration failed)
ALTER TABLE interactions DROP COLUMN function_context;

-- Restore from backup (nuclear option)
psql $DATABASE_PUBLIC_URL < backup_pre_function_context.sql
```

---

### Migration 2: Add Arrows JSONB Column

**Purpose:** Support multi-arrow interactions (Issue #4)

**File:** `migrate_add_arrows.py`

#### 2.1 Backup Database

```bash
# Create new backup after Migration 1
pg_dump -h hostname -U postgres -d railway > backup_pre_arrows.sql
```

#### 2.2 Test Migration Locally

```bash
# Clone production data
psql -h localhost -U postgres -d test_propaths < backup_pre_arrows.sql

# Run migration
DATABASE_URL=postgresql://localhost/test_propaths python migrate_add_arrows.py

# Verify
psql -h localhost -U postgres -d test_propaths -c "\d interactions"
# Should show: arrows | jsonb
```

#### 2.3 Run Production Migration

```bash
railway run python migrate_add_arrows.py
```

**Expected Output:**
```
Migration: Add arrows JSONB column
Connecting to database...
Adding arrows column...
✓ Column added successfully
Migrating existing arrow data...
✓ Converted 1,234 interactions to new format
  - Single arrows: 1,100
  - Complex arrows: 134
Migration complete!
```

#### 2.4 Verify Migration

```sql
-- Check column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'interactions'
  AND column_name = 'arrows';

-- Sample data check (should show both old and new formats)
SELECT
  protein_a_id,
  protein_b_id,
  arrow,  -- Old format (backward compat)
  arrows  -- New format (JSONB)
FROM interactions
WHERE arrows IS NOT NULL
LIMIT 5;

-- Example output:
-- arrow: 'activates'
-- arrows: {"main_to_primary": ["activates"]}

-- Check complex arrows
SELECT
  protein_a_id,
  protein_b_id,
  arrow,
  arrows
FROM interactions
WHERE arrow = 'complex'
LIMIT 5;

-- Example output:
-- arrow: 'complex'
-- arrows: {"main_to_primary": ["activates", "inhibits"]}
```

#### 2.5 Rollback (if needed)

```sql
-- Remove arrows column
ALTER TABLE interactions DROP COLUMN arrows;

-- Restore from backup
psql $DATABASE_PUBLIC_URL < backup_pre_arrows.sql
```

---

### Zero-Downtime Migration Strategy

**Why Zero-Downtime Works:**

1. **Additive Changes:** Both migrations ADD columns, never remove
2. **Backward Compatibility:** Code reads new fields first, falls back to old
3. **Gradual Rollout:** New queries write to new fields; old data remains valid
4. **No Breaking Changes:** Old visualization code still works with `arrow` field

**Migration Timeline:**

```
T+0:  Deploy Migration 1 (function_context)
      - App continues running
      - New queries write to function_context
      - Old data shows null (gracefully handled)

T+30m: Verify no errors in Railway logs

T+1h:  Deploy Migration 2 (arrows)
       - App continues running
       - New queries write to arrows JSONB
       - Old data uses legacy arrow field

T+2h:  Verify new interactions have both fields

T+24h: Query new protein to test end-to-end
       - Should show multi-arrow display
       - Should show context badges
       - CSV export should be clean
```

---

## Post-Deployment Verification

### 1. Health Check

```bash
# Check app is running
curl https://propaths.up.railway.app/

# Should return: 200 OK with landing page HTML
```

### 2. Database Connection

```bash
# Test database query
railway run python -c "
from app import app, db
with app.app_context():
    print('Database connection:', db.engine.url)
    from models import Protein
    count = Protein.query.count()
    print(f'Proteins in database: {count}')
"
```

### 3. API Endpoints

```bash
# Test query endpoint (kicks off pipeline)
curl -X POST https://propaths.up.railway.app/api/query \
  -H 'Content-Type: application/json' \
  -d '{"protein":"VCP"}' \
  -w "\nStatus: %{http_code}\n"

# Expected: {"status": "processing", "message": "Query started for VCP"}

# Poll status (wait 30s-2min)
curl https://propaths.up.railway.app/api/status/VCP

# Expected: {"status": "complete", "protein": "VCP"}

# Fetch results
curl https://propaths.up.railway.app/api/results/VCP | jq '.snapshot_json.main'

# Expected: "VCP"
```

### 4. Feature Verification Checklist

**Issue #1: CSV Export Fix**
- [ ] Open `/api/visualize/VCP`
- [ ] Click interaction → Functions tab
- [ ] Export CSV
- [ ] Verify: One biocascade row per function (no duplicates)

**Issue #2: First-Ring Indirect Interactors**
- [ ] Query protein with indirect interactors (e.g., ATXN3)
- [ ] Click indirect interactor (e.g., TFEB)
- [ ] Verify badge: "INDIRECT (first ring)" or "INDIRECT (via MEDIATOR)"
- [ ] Verify chain display shows full pathway

**Issue #3: Context-Aware Functions**
- [ ] Click interaction with chain context
- [ ] Verify function badge: "DIRECT PAIR" (green) or "CHAIN CONTEXT" (orange)
- [ ] Verify expanded view shows chain pathway
- [ ] Check database: `function_context` column populated

**Issue #4: Multi-Arrow Display**
- [ ] Query VCP (has mixed arrow types)
- [ ] Click interaction with multiple arrows (e.g., VCP → IκBα)
- [ ] **INTERACTION TYPE section** should show:
  ```
  INTERACTION TYPE
    VCP → IκBα:
      [ACTIVATES] [INHIBITS]
  ```
- [ ] **Functions section** should show:
  ```
  Functions (3) [2 arrows]

  --| INHIBITS (2)
  └─ NF-κB Signaling

  --> ACTIVATES (1)
  └─ Protein Degradation
  ```
- [ ] Check database: `arrows` column has JSONB data

**Issue #4 Extension: Graph View Arrow Display**
- [ ] Verify INTERACTION TYPE section shows multiple badges
- [ ] Verify directional labels (Query → Interactor / Interactor → Query)
- [ ] Verify backward compatibility (old proteins show single badge)

### 5. Performance Check

```bash
# Monitor query time
time curl -X POST https://propaths.up.railway.app/api/query \
  -H 'Content-Type: application/json' \
  -d '{"protein":"TEST"}' \
  > /dev/null

# Expected: < 5s response time

# Check Railway metrics
# Dashboard → Metrics → Response time
# Expected: p95 < 2s for /api/results
```

### 6. Error Monitoring

```bash
# Check logs for errors
railway logs --filter error

# Common false positives (ignore):
# - "Retrying Gemini request..." (transient API errors)
# - "Cache miss for..." (expected on first query)

# Real errors to investigate:
# - "DatabaseError: ..."
# - "500 Internal Server Error"
# - "Failed to sync to database"
```

---

## Troubleshooting Guide

### Problem: Migration Script Fails with "Column already exists"

**Cause:** Migration already run, or partial migration

**Solution:**
```sql
-- Check if column exists
SELECT column_name FROM information_schema.columns
WHERE table_name = 'interactions'
  AND column_name = 'function_context';  -- or 'arrows'

-- If exists, migration is complete; skip script
-- If doesn't exist, check error logs for real issue
```

### Problem: Database Connection Refused

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

1. **Check Railway database status**
   ```bash
   railway status
   # Ensure PostgreSQL service is "Active"
   ```

2. **Verify DATABASE_URL environment variable**
   ```bash
   railway variables
   # Should see DATABASE_URL=postgresql://...
   ```

3. **Test direct connection**
   ```bash
   railway connect PostgreSQL
   # Should open psql session
   ```

4. **Firewall/Network Issues (local dev)**
   ```bash
   # Use DATABASE_PUBLIC_URL instead
   psql $DATABASE_PUBLIC_URL
   ```

### Problem: New Queries Don't Show Multi-Arrow Display

**Symptoms:**
- INTERACTION TYPE section still shows single badge
- Functions header shows "2 arrows" badge but INTERACTION TYPE doesn't

**Diagnosis:**

1. **Check if migration ran successfully**
   ```sql
   SELECT arrows FROM interactions WHERE arrows IS NOT NULL LIMIT 1;
   -- Should return JSONB like: {"main_to_primary": ["activates"]}
   ```

2. **Check if new query wrote to arrows column**
   ```sql
   SELECT protein_a_id, protein_b_id, arrow, arrows
   FROM interactions
   WHERE updated_at > NOW() - INTERVAL '1 hour';
   -- Recent queries should have arrows populated
   ```

3. **Check frontend code version**
   - Ensure `visualizer.py:5409-5497` has multi-arrow logic
   - Clear browser cache (Ctrl+F5)
   - Check browser console for JS errors

**Solutions:**

- If `arrows` is null: Backend not writing to new field → check `utils/db_sync.py:282-302`
- If `arrows` has data but UI doesn't show: Frontend not reading → check `visualizer.py:5410`
- If old protein queried: Re-query protein to generate new data

### Problem: CSV Export Still Has Duplicate Rows

**Symptoms:**
- Biocascade repeated for each evidence item

**Diagnosis:**

Check `visualizer.py:8137-8159` for fix:

```javascript
// Line 8137: Should use evIndex === 0 condition
evIndex === 0 ? bioCascadeText : ''
```

**Solution:**

If code is correct but issue persists:
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check Railway deployment logs to ensure latest code deployed

### Problem: Performance Degradation

**Symptoms:**
- Query times > 10s
- Railway dashboard shows high CPU/memory

**Common Causes:**

1. **Too many concurrent queries**
   ```python
   # Check active jobs
   from app import jobs
   print(len([j for j in jobs.values() if j['status'] == 'processing']))
   ```

2. **Database connection pool exhausted**
   ```python
   # In app.py, increase pool size
   app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
       'pool_size': 20,  # Default: 10
       'max_overflow': 30,  # Default: 20
       'pool_timeout': 30,
       'pool_recycle': 3600
   }
   ```

3. **Missing database indexes**
   ```sql
   -- Verify indexes exist
   SELECT indexname, indexdef FROM pg_indexes
   WHERE tablename = 'interactions';

   -- Should have:
   -- idx_interactions_protein_a
   -- idx_interactions_protein_b
   -- idx_interactions_confidence
   ```

4. **Large result sets**
   ```sql
   -- Check for proteins with excessive interactions
   SELECT protein_a_id, COUNT(*) as count
   FROM interactions
   GROUP BY protein_a_id
   ORDER BY count DESC
   LIMIT 10;

   -- If count > 1000, consider pagination or pruning
   ```

**Solutions:**

- Scale up Railway plan (more CPU/memory)
- Implement query rate limiting
- Add Redis cache for frequent queries
- Optimize pruning parameters (lower `max_keep`)

### Problem: Backward Compatibility Broken

**Symptoms:**
- Old proteins (queried before migrations) don't render
- JavaScript errors in console

**Diagnosis:**

```javascript
// Check browser console for:
TypeError: Cannot read property 'main_to_primary' of null
// Means frontend not handling missing arrows field
```

**Solution:**

Ensure fallback logic in `visualizer.py:5484-5488`:

```javascript
} else {
  // Legacy single arrow display (backward compatibility)
  const normalized = normalizeArrow(legacyArrow);
  interactionTypeHTML = createArrowBadge(normalized, arrowColors[normalized]);
}
```

If still broken:
1. Re-query old protein to regenerate with new fields
2. Or run backfill script (see next section)

### Backfill Script (Optional)

**Purpose:** Update old interactions with new fields without re-querying

**Warning:** May override manual edits; backup first

```python
# backfill_interactions.py
from app import app, db
from models import Interaction
import json

with app.app_context():
    interactions = Interaction.query.filter(Interaction.arrows.is_(None)).all()

    for ia in interactions:
        # Migrate arrow -> arrows
        if ia.arrow and not ia.arrows:
            ia.arrows = {
                'main_to_primary': [ia.arrow]
            }

        # Set function_context from data
        if ia.data and 'functions' in ia.data:
            functions = ia.data['functions']
            contexts = {fn.get('_context', {}).get('type', 'direct') for fn in functions}
            if 'chain' in contexts and 'direct' in contexts:
                ia.function_context = 'mixed'
            elif 'chain' in contexts:
                ia.function_context = 'chain'
            else:
                ia.function_context = 'direct'

        db.session.add(ia)

    db.session.commit()
    print(f"Backfilled {len(interactions)} interactions")
```

**Run:**
```bash
railway run python backfill_interactions.py
```

---

## Rollback Procedures

### Complete Rollback (Nuclear Option)

**Use Case:** Critical bug, data corruption, need to revert to pre-migration state

**Steps:**

1. **Stop accepting new queries** (optional, maintenance mode)
   ```python
   # In app.py, add maintenance flag
   MAINTENANCE_MODE = True

   @app.route('/api/query', methods=['POST'])
   def query_protein():
       if MAINTENANCE_MODE:
           return jsonify({'error': 'Under maintenance'}), 503
   ```

2. **Restore database from backup**
   ```bash
   # Find latest backup
   ls -lh backup_*.sql

   # Drop current database (WARNING: DESTRUCTIVE)
   railway connect PostgreSQL
   DROP DATABASE railway;
   CREATE DATABASE railway;

   # Restore
   psql $DATABASE_PUBLIC_URL < backup_pre_function_context.sql
   ```

3. **Revert code changes**
   ```bash
   # Find commit before migrations
   git log --oneline | grep -i "migration"

   # Revert to previous commit
   git revert <commit-hash>
   git push origin main
   ```

4. **Verify rollback**
   ```bash
   # Check schema (should not have new columns)
   railway run python -c "
   from app import db
   from sqlalchemy import inspect
   inspector = inspect(db.engine)
   columns = [c['name'] for c in inspector.get_columns('interactions')]
   print('Columns:', columns)
   assert 'arrows' not in columns
   assert 'function_context' not in columns
   print('✓ Rollback verified')
   "
   ```

### Partial Rollback (Single Migration)

**Use Case:** Migration 2 failed, but Migration 1 is fine

**Steps:**

1. **Revert specific migration**
   ```sql
   ALTER TABLE interactions DROP COLUMN arrows;
   ```

2. **Revert code changes for that feature**
   ```bash
   git revert <commit-hash-for-migration-2>
   ```

3. **Keep Migration 1 changes**
   - `function_context` column remains
   - Context badges continue working

---

## Maintenance Tasks

### Weekly

- [ ] Check Railway logs for errors
- [ ] Monitor database size (Railway dashboard)
- [ ] Review query performance metrics
- [ ] Test sample queries (VCP, ATXN3, etc.)

### Monthly

- [ ] Database backup
- [ ] Clear old cached files (`cache/*.json` older than 90 days)
- [ ] Review and archive logs
- [ ] Check for dependency updates (`pip list --outdated`)

### Quarterly

- [ ] Review Railway plan (scale up/down based on usage)
- [ ] Audit database for orphaned records
- [ ] Performance benchmarking
- [ ] Security audit (dependencies, API keys)

---

## Emergency Contacts

**Railway Support:**
- Dashboard: https://railway.app
- Status: https://status.railway.app
- Docs: https://docs.railway.app

**Database Issues:**
- PostgreSQL Logs: Railway dashboard → PostgreSQL → Logs
- Direct Connection: `railway connect PostgreSQL`

**Code Issues:**
- GitHub: [Your repository URL]
- Issue Tracker: [Your repository]/issues

---

## Deployment Checklist (Quick Reference)

**Pre-Deployment:**
- [ ] Code tested locally
- [ ] Database backup created
- [ ] Migration scripts tested on clone
- [ ] Rollback plan documented
- [ ] Monitoring tools ready

**Deployment:**
- [ ] Push to GitHub / Railway
- [ ] Monitor Railway logs during deploy
- [ ] Run migrations (`migrate_add_function_context.py`, `migrate_add_arrows.py`)
- [ ] Verify schema changes

**Post-Deployment:**
- [ ] Health check (`/`)
- [ ] API test (`/api/query`, `/api/results`)
- [ ] Feature verification (Issues #1-4)
- [ ] Performance check (query times, memory)
- [ ] Error monitoring (Railway logs)

**Rollback (if needed):**
- [ ] Stop accepting queries (maintenance mode)
- [ ] Restore database from backup
- [ ] Revert code changes
- [ ] Verify rollback
- [ ] Resume normal operations

---

## Appendix: SQL Schemas

### Interactions Table (After Migrations)

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    protein_a_id INTEGER NOT NULL REFERENCES proteins(id) ON DELETE CASCADE,
    protein_b_id INTEGER NOT NULL REFERENCES proteins(id) ON DELETE CASCADE,
    confidence NUMERIC(3,2),
    direction VARCHAR(20),
    arrow VARCHAR(50),                -- Legacy (backward compat)
    arrows JSONB,                     -- NEW (Issue #4)
    function_context VARCHAR(20),     -- NEW (Issue #3)
    data JSONB NOT NULL,
    discovered_in_query VARCHAR(50),
    discovery_method VARCHAR(50) DEFAULT 'pipeline',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    CONSTRAINT interaction_unique UNIQUE(protein_a_id, protein_b_id),
    CONSTRAINT interaction_proteins_different CHECK(protein_a_id != protein_b_id)
);

CREATE INDEX idx_interactions_protein_a ON interactions(protein_a_id);
CREATE INDEX idx_interactions_protein_b ON interactions(protein_b_id);
CREATE INDEX idx_interactions_confidence ON interactions(confidence);
```

### Example Data

```sql
-- Old interaction (before migrations)
INSERT INTO interactions (protein_a_id, protein_b_id, arrow, data, ...)
VALUES (1, 20, 'activates', '{"functions": [...]}', ...);

-- Result:
-- arrow: 'activates'
-- arrows: NULL
-- function_context: NULL

-- New interaction (after migrations)
INSERT INTO interactions (protein_a_id, protein_b_id, arrow, arrows, function_context, data, ...)
VALUES (1, 20, 'complex', '{"main_to_primary": ["activates", "inhibits"]}', 'mixed', '{"functions": [...]}', ...);

-- Result:
-- arrow: 'complex'
-- arrows: {"main_to_primary": ["activates", "inhibits"]}
-- function_context: 'mixed'
```

---

**Document Version:** 1.0
**Last Updated:** January 2025
**Maintainer:** ProPaths Team

