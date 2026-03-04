import React from 'react';
import { useNavigate } from 'react-router-dom';

function Header({ username, portalType = "Admin" }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('proctorUser');
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <span className="text-2xl font-bold text-indigo-600">🛡️ ProctorAI+</span>
            <span className="ml-4 font-medium text-gray-700">{portalType} Portal</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm text-gray-600 mr-4">
              Welcome, <span className="font-bold">{username}</span>
            </span>
            <button
              onClick={handleLogout}
              className="px-3 py-2 rounded-md text-sm font-medium text-white bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Header;