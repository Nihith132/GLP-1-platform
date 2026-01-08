# ✅ Version Checker - How Drug Selection Works

## Your Question: Will it only run for selected drugs?

**YES! It will ONLY run automation for the drugs you check/select.** ✅

## How It Works (Step-by-Step)

### 1. **User Interface Selection**
```
┌─────────────────────────────────────────────────┐
│  Version Checker                                │
├─────────────────────────────────────────────────┤
│  [x] Ozempic          (Selected)                │
│  [ ] Saxenda          (Not Selected)            │
│  [x] Wegovy           (Selected)                │
│  [ ] Mounjaro         (Not Selected)            │
│  ... 15 more drugs                              │
├─────────────────────────────────────────────────┤
│  Selected: 2 of 19    [Run Workflow (2)]        │
└─────────────────────────────────────────────────┘
```

### 2. **What Happens When You Click "Run Workflow"**

```typescript
// Frontend collects ONLY the checked drug IDs
const selectedDrugs = [1, 3];  // Only Ozempic and Wegovy

// Sends to backend
watchdogService.triggerManualCheck(selectedDrugs);
// → POST /api/watchdog/trigger with body: [1, 3]
```

### 3. **Backend Processing**

```python
# Backend receives: [1, 3]
drug_ids = [1, 3]  # ONLY the selected ones

# Queries database for ONLY these IDs
query = """
    SELECT id, set_id, name, version
    FROM drug_labels
    WHERE id IN (1, 3)  # ← ONLY selected drugs
"""

# Result: Only 2 drugs
drugs = [
    {"id": 1, "set_id": "abc-123", "name": "Ozempic"},
    {"id": 3, "set_id": "xyz-789", "name": "Wegovy"}
]
```

### 4. **GitHub Actions Trigger**

```python
# Triggers workflow ONLY for selected SET_IDs
set_ids = ["abc-123", "xyz-789"]  # Only 2 drugs

# Each drug gets its own workflow run
dispatcher.trigger_for_multiple_drugs(set_ids)

# Result: 2 workflow runs on GitHub Actions
# ✅ Workflow Run #1: Ozempic (abc-123)
# ✅ Workflow Run #2: Wegovy (xyz-789)
# ❌ NOT triggered for the other 17 drugs
```

## Visual Flow

```
┌──────────────────────────────────────────────────────────────┐
│  YOU SELECT                                                   │
│  ✓ Drug 1 (Ozempic)                                          │
│  ✓ Drug 5 (Wegovy)                                           │
│  ✓ Drug 7 (Saxenda)                                          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  FRONTEND SENDS                                             │
│  drug_ids: [1, 5, 7]    ← ONLY 3 selected                  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  BACKEND QUERIES                                            │
│  SELECT * FROM drug_labels WHERE id IN (1, 5, 7)          │
│  Result: 3 drugs with their SET_IDs                        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS TRIGGERED                                   │
│  ✅ Workflow Run 1: Ozempic (SET_ID: xxx-1)                │
│  ✅ Workflow Run 2: Wegovy (SET_ID: xxx-5)                 │
│  ✅ Workflow Run 3: Saxenda (SET_ID: xxx-7)                │
│                                                             │
│  ❌ Other 16 drugs: NO workflow runs                        │
└─────────────────────────────────────────────────────────────┘
```

## Code Verification

### Frontend Selection Logic
```typescript
// frontend/src/pages/VersionChecker.tsx

const [selectedDrugs, setSelectedDrugs] = useState<number[]>([]);

const toggleDrugSelection = (drugId: number) => {
  setSelectedDrugs((prev) =>
    prev.includes(drugId)
      ? prev.filter((id) => id !== drugId)  // Remove if unchecked
      : [...prev, drugId]                    // Add if checked
  );
};

const runVersionCheckWorkflow = async () => {
  // Only triggers for selectedDrugs array
  await watchdogService.triggerManualCheck(selectedDrugs);
};
```

### Backend Query Logic
```python
# backend/api/routes/watchdog.py

@router.post("/trigger")
async def trigger_manual_watchdog(drug_ids: List[int]):
    # drug_ids = ONLY the selected ones from UI
    
    # Query ONLY for provided drug_ids
    query = text(f"""
        SELECT id, set_id, name, version
        FROM drug_labels
        WHERE id IN ({placeholders})  ← FILTERS by drug_ids
    """)
    
    # Trigger workflow ONLY for these drugs
    set_ids = [drug.set_id for drug in drugs]
    github_results = await dispatcher.trigger_for_multiple_drugs(set_ids)
```

## Example Scenarios

### Scenario 1: Select 1 Drug
```
UI: Check only "Ozempic"
→ selectedDrugs = [1]
→ Backend queries: WHERE id IN (1)
→ GitHub Actions: 1 workflow run
→ Result: Only Ozempic checked
```

### Scenario 2: Select 5 Drugs
```
UI: Check "Ozempic", "Wegovy", "Saxenda", "Mounjaro", "Victoza"
→ selectedDrugs = [1, 3, 5, 7, 9]
→ Backend queries: WHERE id IN (1, 3, 5, 7, 9)
→ GitHub Actions: 5 parallel workflow runs
→ Result: Only these 5 drugs checked
```

### Scenario 3: Select All (using "Select All" button)
```
UI: Click "Select All"
→ selectedDrugs = [1, 2, 3, 4, ..., 19]  (all 19)
→ Backend queries: WHERE id IN (1, 2, 3, ..., 19)
→ GitHub Actions: 19 parallel workflow runs
→ Result: All 19 drugs checked
```

### Scenario 4: Select None
```
UI: No checkboxes checked
→ selectedDrugs = []
→ Button shows: "Run Workflow (0)" and is disabled
→ Result: Can't trigger - validation prevents empty selection
```

## Safety Checks

### Frontend Validation
```typescript
if (selectedDrugs.length === 0) {
  alert('Please select at least one drug label to check');
  return;  // ← Stops execution
}
```

### Backend Validation
```python
if not drug_ids:
    raise HTTPException(status_code=400, detail="No drug IDs provided")

if not drugs:
    raise HTTPException(status_code=404, detail="No drugs found")
```

## UI Indicators

The UI clearly shows what will be triggered:

```
┌─────────────────────────────────────────────────┐
│  Selected: 3 of 19    [Run Workflow (3)]        │
└─────────────────────────────────────────────────┘
         ↑                              ↑
    Shows count              Button shows exact number
```

After clicking:
```
Success: ✅ GitHub Actions workflow triggered successfully!

Triggered for 3 drug(s):
- Ozempic
- Wegovy  
- Saxenda

View progress at:
https://github.com/Nihith132/GLP-1-platform/actions/workflows/watchdog-manual.yml
```

## Summary

| What You Do | What Happens |
|-------------|--------------|
| ✓ Check 2 drugs | ✅ Workflow runs for ONLY those 2 drugs |
| ✓ Check 10 drugs | ✅ Workflow runs for ONLY those 10 drugs |
| ✓ Check all 19 | ✅ Workflow runs for all 19 drugs |
| ✓ Check none | ❌ Button disabled, can't trigger |
| ✓ Uncheck a drug | ✅ That drug removed from trigger list |

**CONFIRMED: The automation will ONLY run for the drugs you explicitly check in the UI.** ✅

The other drugs are completely ignored - they won't be queried, won't trigger workflows, and won't consume any GitHub Actions minutes.
