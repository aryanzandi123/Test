# Fact-Checking Skip Bug Analysis

## Problem
User reports that even with `skip_fact_checking=True`, the pipeline still runs "FACT-CHECKING AND CORRECTING CLAIMS". The skip flag was only partially implemented.

## Root Cause
There are **THREE calls to `fact_check_json()`** in the codebase:

### 1. ✓ Line 1855 (runner.py) - PROTECTED
```python
# STAGE 4: Run claim fact-checker AFTER deduplication
if not skip_fact_checking and FACT_CHECKER_AVAILABLE and api_key:
    fact_checked_payload = fact_check_json(
        deduplicated_payload,
        api_key,
        verbose=False
    )
```
**Status:** Already has proper guard

### 2. ✗ Line 2459 (runner.py) - MISSING GUARD
```python
# STAGE 2.5: Fact-check ONLY new data
if FACT_CHECKER_AVAILABLE:  # <-- WRONG! Missing skip_fact_checking check
    current_step += 1
    update_status(
        text="Fact-checking new claims...",
        current_step=current_step,
        total_steps=total_steps
    )
    
    validated_new_payload = fact_check_json(
        validated_new_payload,
        api_key,
        verbose=False
    )
```
**Status:** UNPROTECTED - runs whenever FACT_CHECKER_AVAILABLE is True
**Location:** In the re-query/expansion flow (around line 2400-2500)
**Impact:** When user clicks to expand an interactor and skip_fact_checking=True, this still executes

### 3. Line 2079 (claim_fact_checker.py) - Test Case
In `__main__` section, not relevant to normal pipeline execution

## Solution
Add `skip_fact_checking` guard to line 2451 in runner.py:
```python
if not skip_fact_checking and FACT_CHECKER_AVAILABLE:
```

This is in the re-query expansion flow where new interactor data is validated.

## Files to Check
- runner.py: 3 locations mentioned in grep (2 calls + 1 import)
- claim_fact_checker.py: Contains print statement "FACT-CHECKING AND CORRECTING CLAIMS FOR {main_protein}" at line 1494
