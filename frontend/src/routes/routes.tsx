import { type RouteObject } from "react-router-dom";
import App from "../App";
import ProtectedRoute from "../components/ProtectedRoute";
import DashboardPage from "../pages/DashboardPage";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import PatientsPage from "../pages/PatientsPage";
import StrokePage from "../pages/StrokePage";
import PredictionHomePage from "../pages/predictions/PredictionHomePage";
import HeartPredictionPage from "../pages/predictions/HeartPredictionPage";
import DiabetesPredictionPage from "../pages/predictions/DiabetesPredictionPage";
import KidneyPredictionPage from "../pages/predictions/KidneyPredictionPage";
import LiverPredictionPage from "../pages/predictions/LiverPredictionPage";
import BreastCancerPredictionPage from "../pages/predictions/BreastCancerPredictionPage";
import ParkinsonPredictionPage from "../pages/predictions/ParkinsonPredictionPage";
import HepatitisPredictionPage from "../pages/predictions/HepatitisPredictionPage";
import HeartFailurePredictionPage from "../pages/predictions/HeartFailurePredictionPage";
import UploadReportPage from "../pages/UploadReportPage";
import ProcessingPage from "../pages/upload/ProcessingPage";
import ReportPreviewPage from "../pages/upload/ReportPreviewPage";
import DrugSafetyPage from "../pages/DrugSafetyPage";
import KnowledgePage from "../pages/KnowledgePage";
import ChatPage from "../pages/ChatPage";
import ReportsPage from "../pages/ReportsPage";
import NotFoundPage from "../pages/NotFoundPage";
import SettingsPage from "../pages/settings/SettingsPage";
import ProfilePage from "../pages/settings/ProfilePage";
import ModelEvaluationPage from "../pages/dashboard/ModelEvaluationPage";
import XaiDashboardPage from "../pages/dashboard/XaiDashboardPage";
import GuidelinesPage from "../pages/dashboard/GuidelinesPage";
import WorkflowPage from "../pages/dashboard/WorkflowPage";


export const routes: RouteObject[] = [
  {
    path: "/",
    element: <App />,
    children: [
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: "patients", element: <PatientsPage /> },
          { path: "predictions", element: <PredictionHomePage /> },
          { path: "heart-disease", element: <HeartPredictionPage /> },
          { path: "diabetes", element: <DiabetesPredictionPage /> },
          { path: "kidney-disease", element: <KidneyPredictionPage /> },
          { path: "liver-disease", element: <LiverPredictionPage /> },
          { path: "breast-cancer", element: <BreastCancerPredictionPage /> },
          { path: "parkinsons", element: <ParkinsonPredictionPage /> },
          { path: "hepatitis", element: <HepatitisPredictionPage /> },
          { path: "heart-failure", element: <HeartFailurePredictionPage /> },
          { path: "stroke", element: <StrokePage /> },
          { path: "upload-report", element: <UploadReportPage /> },
          { path: "upload-report/processing", element: <ProcessingPage /> },
          { path: "upload-report/preview", element: <ReportPreviewPage /> },
          { path: "drug-safety", element: <DrugSafetyPage /> },
          { path: "knowledge", element: <KnowledgePage /> },
          { path: "chat", element: <ChatPage /> },
          { path: "reports", element: <ReportsPage /> },
          { path: "settings", element: <SettingsPage /> },
          { path: "settings/profile", element: <ProfilePage /> },
          { path: "model-evaluation", element: <ModelEvaluationPage /> },
          { path: "xai", element: <XaiDashboardPage /> },
          { path: "guidelines", element: <GuidelinesPage /> },
          { path: "workflow", element: <WorkflowPage /> },

        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
];
