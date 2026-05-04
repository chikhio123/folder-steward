import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import ScanPage from "./pages/ScanPage";
import FileListPage from "./pages/FileListPage";
import DuplicatePage from "./pages/DuplicatePage";
import SuggestionPage from "./pages/SuggestionPage";
import OperationHistoryPage from "./pages/OperationHistoryPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}
