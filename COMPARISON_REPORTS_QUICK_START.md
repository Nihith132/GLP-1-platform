# Comparison Workspace Reports - Quick Start Guide

> **Reference**: For complete details, see `REPORTS_IMPLEMENTATION_COMPLETE_GUIDE.md`

## 🎯 Goal
Implement save/load reports functionality for Comparison Workspace (similar to Analysis Workspace).

## ✅ What's Already Done
- Analysis Workspace reports: **FULLY WORKING**
- Reports page: **COMPLETE**
- Backend API: **READY** (JSONB supports any structure)
- Database: **READY** (no changes needed)

## 🚀 What You Need to Build

### Step 1: Create Comparison Store
**File**: `frontend/src/store/comparisonWorkspaceStore.ts` (NEW)

```typescript
import { create } from 'zustand';
import { reportService } from '@/services/reportService';

interface ComparisonWorkspaceStore {
  // Multiple drugs
  leftDrugId: number | null;
  leftDrugName: string;
  rightDrugId: number | null;
  rightDrugName: string;
  
  // Side-specific data
  leftHighlights: Highlight[];
  rightHighlights: Highlight[];
  leftScrollPosition: number;
  rightScrollPosition: number;
  
  // Shared data
  comparisonNotes: Record<string, Note>;
  flaggedChats: ChatMessage[];
  
  // Report actions
  saveAsComparisonReport: async (title: string, description: string) => {
    const state = get();
    const workspaceState = {
      drug_ids: [state.leftDrugId, state.rightDrugId],
      drug_names: [state.leftDrugName, state.rightDrugName],
      left_drug_id: state.leftDrugId,
      right_drug_id: state.rightDrugId,
      left_highlights: state.leftHighlights,
      right_highlights: state.rightHighlights,
      comparison_notes: state.comparisonNotes,
      flaggedChats: state.flaggedChats,
      scroll_positions: {
        left: state.leftScrollPosition,
        right: state.rightScrollPosition
      }
    };
    
    await reportService.createReport({
      title,
      description,
      report_type: 'comparison',  // ⭐ Important!
      workspace_state: workspaceState,
    });
  },
  
  loadComparisonReport: (report) => {
    const ws = report.workspace_state;
    set({
      leftDrugId: ws.left_drug_id,
      leftDrugName: ws.drug_names?.[0] || '',
      rightDrugId: ws.right_drug_id,
      rightDrugName: ws.drug_names?.[1] || '',
      leftHighlights: ws.left_highlights || [],
      rightHighlights: ws.right_highlights || [],
      comparisonNotes: ws.comparison_notes || {},
      flaggedChats: ws.flaggedChats || [],
      leftScrollPosition: ws.scroll_positions?.left || 0,
      rightScrollPosition: ws.scroll_positions?.right || 0,
    });
  },
}

export const useComparisonWorkspaceStore = create<ComparisonWorkspaceStore>(...);
```

### Step 2: Add Save Button
**File**: `frontend/src/pages/ComparisonWorkspace.tsx` (MODIFY)

```tsx
import { SaveReportModal } from '@/components/SaveReportModal';
import { useComparisonWorkspaceStore } from '@/store/comparisonWorkspaceStore';

export function ComparisonWorkspace() {
  const [showSaveModal, setShowSaveModal] = useState(false);
  const { saveAsComparisonReport } = useComparisonWorkspaceStore();
  
  return (
    <div>
      {/* Existing UI */}
      
      <Button onClick={() => setShowSaveModal(true)}>
        <Save className="h-4 w-4 mr-2" />
        Save Comparison Report
      </Button>
      
      <SaveReportModal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        onSave={saveAsComparisonReport}
        reportType="comparison"  // ⭐ Add this prop
      />
    </div>
  );
}
```

### Step 3: Update SaveReportModal
**File**: `frontend/src/components/SaveReportModal.tsx` (MODIFY)

```tsx
interface SaveReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (title: string, description: string) => Promise<void>;
  reportType?: 'analysis' | 'comparison';  // ⭐ Add this
}

export function SaveReportModal({ 
  reportType = 'analysis',  // Default to analysis
  ...props 
}: SaveReportModalProps) {
  return (
    <Modal {...props}>
      <h2>
        Save {reportType === 'comparison' ? 'Comparison' : 'Analysis'} Report
      </h2>
      {/* Rest stays the same */}
    </Modal>
  );
}
```

### Step 4: Update Reports Page
**File**: `frontend/src/pages/Reports.tsx` (MODIFY)

```tsx
const handleLoadReport = async (reportId: string | number) => {
  const report = await reportService.getReportById(reportId);
  sessionStorage.setItem('pendingReportLoad', JSON.stringify(report));
  
  // ⭐ Route based on report type
  if (report.report_type === 'comparison') {
    const drugIds = report.workspace_state.drug_ids || [];
    navigate(`/comparison?drugs=${drugIds.join(',')}&loadReport=${reportId}`);
  } else {
    const drugId = report.workspace_state.drug_id;
    navigate(`/analysis/${drugId}?loadReport=${reportId}`);
  }
};
```

### Step 5: Add Load Logic to Comparison Workspace
**File**: `frontend/src/pages/ComparisonWorkspace.tsx` (MODIFY)

```tsx
import { useComparisonWorkspaceStore } from '@/store/comparisonWorkspaceStore';

export function ComparisonWorkspace() {
  const { loadComparisonReport } = useComparisonWorkspaceStore();
  
  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const reportId = urlParams.get('loadReport');
    
    if (reportId) {
      const reportData = sessionStorage.getItem('pendingReportLoad');
      if (reportData) {
        const report = JSON.parse(reportData);
        loadComparisonReportData(report);
        sessionStorage.removeItem('pendingReportLoad');
      }
    }
  }, [location.search]);
  
  const loadComparisonReportData = (report: Report) => {
    // Load report state into store
    loadComparisonReport(report);
    
    // Load drug data
    const { left_drug_id, right_drug_id } = report.workspace_state;
    if (left_drug_id) loadLeftDrug(left_drug_id);
    if (right_drug_id) loadRightDrug(right_drug_id);
  };
  
  // Wait for drugs to load, then restore state
  useEffect(() => {
    if (leftDrug && rightDrug && !isLoading) {
      // Highlights will render from store
      // Restore scroll positions
      setTimeout(() => {
        const { leftScrollPosition, rightScrollPosition } = 
          useComparisonWorkspaceStore.getState();
        // Scroll left panel
        document.querySelector('.left-panel')?.scrollTo(0, leftScrollPosition);
        // Scroll right panel
        document.querySelector('.right-panel')?.scrollTo(0, rightScrollPosition);
      }, 500);
    }
  }, [leftDrug, rightDrug, isLoading]);
}
```

## 🔑 Critical Points

### 1. snake_case for Backend
```typescript
// ✅ Always convert for backend
const workspaceState = {
  drug_ids: [...],        // snake_case
  drug_names: [...],      // snake_case
  left_highlights: [...], // snake_case
};
```

### 2. Multiple Drugs
```typescript
// Analysis: Single drug
{ drug_id: 1, drug_name: "Ozempic" }

// Comparison: Multiple drugs
{ 
  drug_ids: [1, 2],
  drug_names: ["Ozempic", "Wegovy"],
  left_drug_id: 1,
  right_drug_id: 2
}
```

### 3. Report Type
```typescript
report_type: 'comparison'  // Not 'analysis'
```

### 4. sessionStorage Pattern
```typescript
// Save before navigate
sessionStorage.setItem('pendingReportLoad', JSON.stringify(report));

// Load after navigate
const reportData = sessionStorage.getItem('pendingReportLoad');
if (reportData) {
  const report = JSON.parse(reportData);
  loadComparisonReportData(report);
  sessionStorage.removeItem('pendingReportLoad');  // Clean up!
}
```

## 🧪 Testing Checklist

- [ ] Create comparison report with 2 drugs
- [ ] Save shows success message
- [ ] Report appears on Reports page
- [ ] Report shows correct drug names
- [ ] Report type badge shows "comparison"
- [ ] Load report from Reports page
- [ ] Navigates to comparison workspace
- [ ] Both drugs load
- [ ] Highlights appear on correct sides
- [ ] Notes restore
- [ ] Flagged chats restore
- [ ] Scroll positions restore
- [ ] Delete comparison report works

## 🚨 Common Mistakes to Avoid

1. ❌ Forgetting `report_type: 'comparison'`
2. ❌ Not cleaning up sessionStorage
3. ❌ Using camelCase instead of snake_case for backend
4. ❌ Not waiting for drug data before restoring state
5. ❌ Forgetting to update Reports page routing
6. ❌ Not handling both report types in Reports page

## 📚 Reference Implementation

Look at these files for patterns:
- `frontend/src/store/workspaceStore.ts` - Your template
- `frontend/src/pages/AnalysisWorkspace.tsx` - Load pattern
- `frontend/src/pages/Reports.tsx` - Routing logic

## 🎯 Expected Timeline

- Step 1 (Store): 30-45 minutes
- Step 2 (Save button): 15 minutes
- Step 3 (Modal update): 10 minutes
- Step 4 (Reports routing): 15 minutes
- Step 5 (Load logic): 30-45 minutes
- Testing: 30 minutes

**Total: ~2-3 hours**

## ✅ Success Criteria

You're done when:
1. ✅ Can save comparison report from Comparison Workspace
2. ✅ Comparison reports show on Reports page
3. ✅ Can load comparison report
4. ✅ All state restores correctly (drugs, highlights, notes, chats, scroll)
5. ✅ Can delete comparison report
6. ✅ Both analysis and comparison reports work together

---

**You've got this!** The Analysis Workspace implementation is your complete guide. Comparison is just the multi-drug version. 🚀
