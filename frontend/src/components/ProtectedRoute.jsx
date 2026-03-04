import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

/**
 * This component checks if a user is logged in and has the correct role.
 * @param {object} props
 * @param {string} props.role - The role required to access this route ('admin' or 'student').
 */
function ProtectedRoute({ role }) {
  const user = JSON.parse(localStorage.getItem('proctorUser'));

  // 1. Check if user exists
  if (!user) {
    // Not logged in, redirect to login
    return <Navigate to="/login" replace />;
  }

  // 2. Check if user has the required role
  if (user.role !== role) {
    // Logged in, but wrong role. Redirect to their *correct* dashboard.
    const redirectTo = user.role === 'admin' ? '/admin/dashboard' : '/student/dashboard';
    return <Navigate to={redirectTo} replace />;
  }

  // 3. If all checks pass, render the child component (e.g., <AdminDashboard />)
  return <Outlet />;
}

export default ProtectedRoute;