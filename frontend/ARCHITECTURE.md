# GLP-1 Platform - Complete Frontend Architecture

## 🎨 **DESIGN PHILOSOPHY**

### Visual Theme
- **Light Mode**: Clean white/off-white background (#FAFAFA)
- **Dark Mode**: Deep charcoal (#0F172A) with blue accents
- **Primary Color**: Professional Blue (#3B82F6)
- **Accent**: Teal (#14B8A6) for highlights
- **Typography**: Inter font family

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│  Header (Logo, Search, User Menu, Dark Mode Toggle)    │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ Sidebar  │           Main Content Area                  │
│          │                                              │
│ - Dashboard    (Dynamic based on selected route)       │
│ - Analytics                                            │
│ - Comparison                                           │
│ - Reports                                              │
│ - Version                                              │
│   Checker                                              │
│ - Chat                                                 │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

## 📁 **COMPLETE FILE STRUCTURE**

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx          # Collapsible navigation
│   │   │   ├── Header.tsx           # Top bar with search
│   │   │   ├── Layout.tsx           # Main layout wrapper
│   │   │   └── DarkModeToggle.tsx   # Theme switcher
│   │   ├── ui/
│   │   │   ├── Button.tsx           # Base button component
│   │   │   ├── Card.tsx             # Card container
│   │   │   ├── Input.tsx            # Form input
│   │   │   ├── Select.tsx           # Dropdown select
│   │   │   ├── Dialog.tsx           # Modal dialog
│   │   │   ├── Tabs.tsx             # Tab component
│   │   │   ├── Badge.tsx            # Status badge
│   │   │   ├── Tooltip.tsx          # Hover tooltip
│   │   │   ├── Checkbox.tsx         # Checkbox input
│   │   │   └── Spinner.tsx          # Loading indicator
│   │   └── features/
│   │       ├── DrugCard.tsx         # Drug display card
│   │       ├── SectionViewer.tsx    # Label section viewer
│   │       ├── EntityHighlight.tsx  # NER entity highlight
│   │       ├── ComparisonView.tsx   # Side-by-side compare
│   │       ├── DiffViewer.tsx       # Text diff display
│   │       ├── ReportCard.tsx       # Report list item
│   │       ├── VersionCheckCard.tsx # Version status card
│   │       ├── ChatMessage.tsx      # Chat bubble
│   │       └── AnalyticsChart.tsx   # Chart component
│   ├── pages/
│   │   ├── Dashboard.tsx            # Main dashboard (drug list)
│   │   ├── Analytics.tsx            # Platform analytics
│   │   ├── Comparison.tsx           # Drug comparison tool
│   │   ├── Reports.tsx              # Saved reports list
│   │   ├── ReportDetail.tsx         # Individual report view
│   │   ├── VersionChecker.tsx       # Version monitoring tool
│   │   └── NotFound.tsx             # 404 page
│   ├── hooks/
│   │   ├── useDrugs.ts              # Drug data hook
│   │   ├── useSearch.ts             # Search functionality
│   │   ├── useReports.ts            # Reports management
│   │   ├── useVersionCheck.ts       # Version checker
│   │   ├── useAnalytics.ts          # Analytics data
│   │   └── useDarkMode.ts           # Theme management
│   ├── store/
│   │   ├── appStore.ts              # Global app state (Zustand)
│   │   ├── drugStore.ts             # Drug selection state
│   │   └── chatStore.ts             # Chat history state
│   ├── services/
│   │   ├── api.ts                   # Axios instance
│   │   ├── drugService.ts           # Drug API calls
│   │   ├── searchService.ts         # Search API calls
│   │   ├── comparisonService.ts     # Comparison API calls
│   │   ├── reportService.ts         # Report API calls
│   │   ├── analyticsService.ts      # Analytics API calls
│   │   ├── chatService.ts           # Chat API calls
│   │   └── versionService.ts        # Version check API
│   ├── utils/
│   │   ├── formatters.ts            # Date, number formatters
│   │   ├── validators.ts            # Form validation
│   │   └── constants.ts             # App constants
│   ├── lib/
│   │   └── utils.ts                 # Utility functions
│   ├── types/
│   │   └── index.ts                 # TypeScript types
│   ├── App.tsx                      # Main app component
│   ├── main.tsx                     # Entry point
│   └── index.css                    # Global styles
├── .env.example
├── .gitignore
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── setup.sh
└── README.md
```

## 🎯 **PAGE SPECIFICATIONS**

### 1. Dashboard (Home)
**Purpose**: Browse and select drug labels

**Features**:
- Grid/List view toggle
- Search bar (real-time)
- Filter by manufacturer, version
- Sort by name, date updated
- Quick actions: View, Compare, Analyze

**API Endpoints**:
- GET /api/drugs - List all drugs
- GET /api/drugs/{id} - Get drug details

### 2. Analytics
**Purpose**: Platform-wide statistics

**Features**:
- Total drugs, sections, entities count
- Entity distribution chart (Bar/Pie)
- Drug update timeline
- Most common entities list
- Data export button

**API Endpoints**:
- GET /api/analytics/platform - Platform stats
- GET /api/analytics/entities - Entity breakdown

### 3. Comparison Workspace
**Purpose**: Side-by-side drug comparison

**Features**:
- Drug selector (dropdown with search)
- Section-by-section comparison
- Highlight differences (colors)
- Similarity score display
- Export comparison report
- Save as report button

**API Endpoints**:
- POST /api/compare - Compare two drugs
- POST /api/compare/sections - Section comparison

### 4. Reports
**Purpose**: Manage saved analysis reports

**Features**:
- Report list (cards/table)
- Filter by type, date, tags
- Search reports
- Click to open report detail
- Delete report button
- Export report (PDF/Word)

**API Endpoints**:
- GET /api/reports - List reports
- GET /api/reports/{id} - Get report detail
- POST /api/reports - Create report
- DELETE /api/reports/{id} - Delete report
- GET /api/reports/{id}/export - Export report

### 5. Version Checker
**Purpose**: Manual version monitoring

**Features**:
- Drug selection (multi-select checkboxes)
- "Check Now" button
- Status display per drug:
  - ✅ Up to date
  - 🆕 New version available
  - ❌ Error
- Version history table
- Last check timestamp
- Auto-refresh option

**API Endpoints**:
- POST /api/version-check/manual - Manual version check
- GET /api/version-check/history - Version history
- GET /api/drugs - Get enabled drugs

### 6. Chat Interface (Floating or Separate Page)
**Purpose**: AI-powered Q&A

**Features**:
- Chat messages (user/assistant)
- Message input with send button
- Source citations
- Clear chat button
- Export conversation

**API Endpoints**:
- POST /api/chat/query - Send chat message

## 🎨 **COMPONENT DESIGN PATTERNS**

### Sidebar Navigation
```tsx
- Logo at top
- Collapsible (hamburger icon)
- Active state highlighting
- Icons + labels
- Footer with version info
```

### Drug Cards
```tsx
Card {
  - Drug name (h3)
  - Manufacturer (subtitle)
  - Version badge
  - Last updated date
  - Actions: View, Compare, Analyze
}
```

### Comparison View
```tsx
Two-column layout:
  Left: Drug A sections
  Right: Drug B sections
  Middle: Diff indicator
  Colors: Green (added), Red (removed), Yellow (modified)
```

## 🔄 **STATE MANAGEMENT**

### Zustand Store Structure
```typescript
appStore:
  - theme: 'light' | 'dark'
  - sidebarCollapsed: boolean
  - notifications: Notification[]

drugStore:
  - selectedDrugs: Drug[]
  - comparisonDrugs: [Drug, Drug] | null
  - filters: FilterState

chatStore:
  - messages: ChatMessage[]
  - isLoading: boolean
```

## 🎯 **KEY USER FLOWS**

### Flow 1: Compare Two Drugs
1. Navigate to Dashboard
2. Select first drug → "Compare" button
3. Select second drug
4. Automatically navigate to Comparison page
5. View side-by-side differences
6. Save as report (optional)

### Flow 2: Check Version Updates
1. Navigate to Version Checker
2. See list of all 19 drugs with checkboxes
3. Select drugs to check (or "Select All")
4. Click "Check Now" button
5. See real-time status updates
6. View new version details if available

### Flow 3: View Analytics
1. Navigate to Analytics
2. See dashboard with charts and stats
3. Click on entity type to see details
4. Export data if needed

## 🎨 **COLOR CODING**

### Status Colors
- Success: #10B981 (Green)
- Warning: #F59E0B (Yellow)
- Error: #EF4444 (Red)
- Info: #3B82F6 (Blue)
- Neutral: #6B7280 (Gray)

### Diff Colors (Comparison)
- Added: #DCFCE7 (Light Green)
- Removed: #FEE2E2 (Light Red)
- Modified: #FEF3C7 (Light Yellow)
- Unchanged: #F3F4F6 (Light Gray)

## 📱 **RESPONSIVE BREAKPOINTS**

- Mobile: < 640px (sidebar hidden by default)
- Tablet: 640px - 1024px (sidebar collapsible)
- Desktop: > 1024px (sidebar always visible)

## ⚡ **PERFORMANCE OPTIMIZATIONS**

1. **Code Splitting**: Lazy load pages
2. **Memoization**: React.memo for expensive components
3. **Virtual Scrolling**: For large drug lists
4. **Debounced Search**: 300ms delay
5. **Image Optimization**: WebP format
6. **Bundle Size**: Keep under 500KB (gzipped)

## 🚀 **DEPLOYMENT CHECKLIST**

- [ ] Build project: `npm run build`
- [ ] Test production build: `npm run preview`
- [ ] Update API_BASE_URL for production
- [ ] Configure CORS on backend
- [ ] Deploy to hosting (Vercel/Netlify/S3)
- [ ] Setup CDN for assets
- [ ] Enable gzip compression
- [ ] Configure caching headers
- [ ] Test on multiple browsers/devices
- [ ] Performance audit (Lighthouse)

---

**This architecture ensures**:
✅ Clean, professional UI
✅ Excellent UX with intuitive navigation
✅ Full backend integration
✅ Responsive design
✅ Dark mode support
✅ Production-ready code
✅ Showcase quality for leadership

**Next Steps**: Run installation and start development server!
