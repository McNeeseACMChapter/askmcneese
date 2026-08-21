import { Navigate, Route, Routes } from "react-router-dom";
import { AcmAppShell } from "./components/shell/AcmAppShell";
import { AdministrationPage } from "./pages/AdministrationPage";
import { ApprovalDetailPage } from "./pages/ApprovalDetailPage";
import { ArchivedRecordPage } from "./pages/ArchivedRecordPage";
import { AuditPage } from "./pages/AuditPage";
import { CommunicationsPage } from "./pages/CommunicationsPage";
import { DataAccessPage } from "./pages/DataAccessPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { EmptyStatePage } from "./pages/EmptyStatePage";
import { EventsPage } from "./pages/EventsPage";
import { FinancePage } from "./pages/FinancePage";
import { FixtureGalleryPage } from "./pages/FixtureGalleryPage";
import { GovernancePage } from "./pages/GovernancePage";
import { HomePage } from "./pages/HomePage";
import { LoadingPage } from "./pages/LoadingPage";
import { LoginPage } from "./pages/LoginPage";
import { MeetingsPage } from "./pages/MeetingsPage";
import { MembersPage } from "./pages/MembersPage";
import { MyWorkPage } from "./pages/MyWorkPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { OfflinePage } from "./pages/OfflinePage";
import { PermissionDeniedPage } from "./pages/PermissionDeniedPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SgaPage } from "./pages/SgaPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AcmAppShell />}>
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/my-work" element={<MyWorkPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
        <Route path="/approvals/:approvalId" element={<ApprovalDetailPage />} />
        <Route path="/meetings" element={<MeetingsPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/members" element={<MembersPage />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/sga" element={<SgaPage />} />
        <Route path="/finance" element={<FinancePage />} />
        <Route path="/communications" element={<CommunicationsPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/data-access" element={<DataAccessPage />} />
        <Route path="/administration" element={<AdministrationPage />} />
        <Route path="/audit" element={<AuditPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/fixtures" element={<FixtureGalleryPage />} />
        <Route path="/fixtures/permission-denied" element={<PermissionDeniedPage />} />
        <Route path="/fixtures/empty" element={<EmptyStatePage />} />
        <Route path="/fixtures/archived" element={<ArchivedRecordPage />} />
        <Route path="/fixtures/offline" element={<OfflinePage />} />
        <Route path="/fixtures/loading" element={<LoadingPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/home" replace />} />
    </Routes>
  );
}
