import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Import Pages
import LoginPage from "./pages/LoginPage";
import StudentDashboard from "./pages/StudentDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import LiveProctorDashboard from "./pages/LiveProctorDashboard"; // ADD THIS
import ExamPage from "./pages/ExamPage";
import LandingPage from "./pages/LandingPage";
import AboutUsPage from "./pages/AboutUsPage";

// Import Components
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/about" element={<AboutUsPage />} />

      {/* Admin Protected Routes */}
      <Route element={<ProtectedRoute role="admin" />}>
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/live" element={<LiveProctorDashboard />} />{" "}
        {/* ADD THIS */}
      </Route>

      {/* Student Protected Routes */}
      <Route element={<ProtectedRoute role="student" />}>
        <Route path="/student/dashboard" element={<StudentDashboard />} />
        <Route path="/exam/:examId" element={<ExamPage />} />
      </Route>

      {/* A catch-all route */}
      <Route path="*" element={<h1>404: Page Not Found</h1>} />
    </Routes>
  );
}

export default App;
