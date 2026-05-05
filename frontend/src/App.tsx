import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { useEffect } from "react";
import toast from "react-hot-toast";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import ScanPage from "./pages/ScanPage";
import FileListPage from "./pages/FileListPage";
import DuplicatePage from "./pages/DuplicatePage";
import SuggestionPage from "./pages/SuggestionPage";
import OperationHistoryPage from "./pages/OperationHistoryPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  useEffect(() => {
    if (window.electronAPI?.onBackendError) {
      window.electronAPI.onBackendError((message) => {
        toast.error(`核心服务启动失败: ${message}\n请检查环境是否完整或端口是否被占用。`, { duration: 8000 });
      });
    }
  }, []);

  return (
    <>
      <Toaster
        position="top-center"
        toastOptions={{
          style: {
            background: '#ffffff',
            color: '#1e293b',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.05)',
            border: '1px solid #f1f5f9',
            fontSize: '14px',
            fontWeight: 500,
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#f43f5e',
              secondary: '#fff',
            },
          },
        }}
      />
      <HashRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="scan" element={<ScanPage />} />
            <Route path="files" element={<FileListPage />} />
            <Route path="duplicates" element={<DuplicatePage />} />
            <Route path="suggestions" element={<SuggestionPage />} />
            <Route path="operations" element={<OperationHistoryPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </HashRouter>
    </>
  );
}
