import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ScanPage } from './pages/ScanPage';
import { RepositoryPage } from './pages/RepositoryPage';
import { ReportPage } from './pages/ReportPage';
import { AdminRulesPage } from './pages/AdminRulesPage';

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-600 font-mono">Initializing VisionX...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const handleNavigateToReport = (scanId: string) => {
    setSelectedScanId(scanId);
    setActiveTab('reports');
    setIsMobileNavOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans w-full overflow-x-hidden">
      <Navbar onToggleSidebar={() => setIsMobileNavOpen((prev) => !prev)} />

      <div className="flex flex-1 relative min-w-0 w-full overflow-x-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isOpen={isMobileNavOpen}
          onClose={() => setIsMobileNavOpen(false)}
        />

        <main className="flex-1 p-3 sm:p-5 md:p-6 min-w-0 w-full md:overflow-y-auto md:max-h-[calc(100vh-4rem)]">
          {activeTab === 'dashboard' && (
            <DashboardPage
              onViewScan={handleNavigateToReport}
              onNewScan={() => setActiveTab('scan')}
            />
          )}

          {activeTab === 'scan' && (
            <ScanPage onViewReport={handleNavigateToReport} />
          )}

          {activeTab === 'repository' && (
            <RepositoryPage
              onViewReport={handleNavigateToReport}
              onInspectProduct={() => setActiveTab('scan')}
            />
          )}

          {activeTab === 'reports' && (
            <ReportPage
              scanId={selectedScanId}
              onBackToScan={() => setActiveTab('scan')}
            />
          )}

          {activeTab === 'rules' && <AdminRulesPage />}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
