import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Analytics } from './pages/Analytics';
import { Comparison } from './pages/Comparison';
import { ComparisonWorkspace } from './pages/ComparisonWorkspace';
import { Reports } from './pages/Reports';
import { ReportDetail } from './pages/ReportDetail';
import { VersionChecker } from './pages/VersionChecker';
import { AnalysisWorkspace } from './pages/AnalysisWorkspace';
import { NotFound } from './pages/NotFound';
import PrintedLabelView from './components/features/PrintedLabelView';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="analysis/:drugId" element={<AnalysisWorkspace />} />
          <Route path="label/:drugId" element={<PrintedLabelView />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="comparison" element={<Comparison />} />
          <Route path="comparison/:sourceId/:competitorId" element={<ComparisonWorkspace />} />
          <Route path="reports" element={<Reports />} />
          <Route path="reports/:id" element={<ReportDetail />} />
          <Route path="version-checker" element={<VersionChecker />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
