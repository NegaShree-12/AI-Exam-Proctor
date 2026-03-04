import React from 'react';
import { Link } from 'react-router-dom'; // Added for the Header links

// --- Header Component (Inlined to fix error) ---
const LandingHeader = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 shadow-md backdrop-blur-lg">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo and Title (Left Side) */}
          <Link to="/" className="flex-shrink-0 flex items-center transition-transform duration-300 hover:scale-105">
            <span className="text-4xl font-bold">
              <span className="mr-2 drop-shadow-md">🛡️</span>
              <span
                className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-700 drop-shadow-sm"
                style={{ textShadow: '0 1px 2px rgba(0,0,0,0.1)' }}
              >
                ProctorAI+
              </span>
            </span>
          </Link>

          {/* Nav Links & Auth Buttons (Right Side) */}
          <div className="hidden md:flex md:items-center md:space-x-8">
            {/* Navigation Links */}
            <div className="flex items-center space-x-6">
              <a
                href="/#features" // Links to the features section on the homepage
                className="text-lg font-medium text-gray-600 hover:text-indigo-600 transition-colors duration-200"
              >
                Features
              </a>
              <Link
                to="/about" // Links to this About Us page
                className="text-lg font-medium text-gray-600 hover:text-indigo-600 transition-colors duration-200"
              >
                About Us
              </Link>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center space-x-3">
              <Link
                to="/login"
                className="px-5 py-2 text-base font-medium text-indigo-600 bg-indigo-100 rounded-md hover:bg-indigo-200 transition-colors duration-200"
              >
                Log in
              </Link>
              <Link
                to="/login?mode=register" // This links to the registration page
                className="px-5 py-2 text-base font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors duration-200"
              >
                Sign up
              </Link>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};

// --- Footer Component (Inlined to fix error) ---
const LandingFooter = () => {
  return (
    <footer className="bg-gray-900 text-gray-400">
      <div className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8 text-center">
        {/* Title */}
        <span className="text-xl font-bold">
          <span className="mr-1">🛡️</span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">
            ProctorAI+
          </span>
        </span>
        {/* Copyright */}
        <p className="text-base mt-2">
          &copy; 2025 ProctorAI+. All rights reserved.
        </p>
      </div>
    </footer>
  );
};

// --- Icon components (Inlined to fix errors) ---
// These are defined here so the page is self-contained.
const CpuIcon = ({ className = '' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><path d="M15 2v2" /><path d="M15 20v2" /><path d="M2 15h2" /><path d="M2 9h2" /><path d="M20 15h2" /><path d="M20 9h2" /><path d="M9 2v2" /><path d="M9 20v2" /></svg>
);
const UserCheckIcon = ({ className = '' }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><polyline points="16 11 18 13 22 9" /></svg>
);
// ShieldCheckIcon was imported but not used, so it's removed.


// --- Main About Us Page Component ---
function AboutUsPage() {
  return (
    <div className="min-h-screen bg-white font-sans">
      <LandingHeader />

      {/* Page Content */}
      <main className="pt-20"> {/* Offset for fixed header */}
        
        {/* Hero Section for About Page */}
        <div className="bg-gray-50 py-24 sm:py-32">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="text-base font-semibold text-indigo-600 uppercase tracking-wide">
              About Us
            </h1>
            <p className="mt-2 text-4xl lg:text-5xl font-extrabold text-gray-900">
              Building a Fairer, More Secure Future for Education
            </p>
            <p className="mt-6 text-xl text-gray-600 leading-relaxed">
              ProctorAI+ is a next-generation, AI-powered exam proctoring system designed with a
              privacy-first philosophy. We go beyond simple gaze tracking to build a holistic
              understanding of the test-taking environment.
            </p>
          </div>
        </div>

        {/* Core Philosophy Section */}
        <div className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="lg:text-center">
              <h2 className="text-3xl lg:text-4xl font-extrabold text-gray-900">
                Our Core Philosophy
              </h2>
              <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-600">
                We believe security and student privacy are not mutually exclusive.
                Our system is built on two unshakeable pillars.
              </p>
            </div>

            <div className="mt-20 grid md:grid-cols-2 gap-16 items-start">
              {/* Pillar 1: Privacy */}
              <div className="flex flex-col items-center text-center p-6 border border-gray-100 rounded-xl shadow-lg">
                <div className="flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">
                  <CpuIcon className="w-10 h-10" />
                </div>
                <h3 className="mt-6 text-2xl font-bold text-gray-900">
                  Privacy-First Edge Processing
                </h3>
                <p className="mt-4 text-lg text-gray-600">
                  Our system's strongest feature is its commitment to privacy. All intensive AI processing occurs locally on the user's device. Sensitive video and audio data **never** leave the student's computer. Only anonymized, encrypted alerts are sent to the proctor, guaranteeing student privacy and building a system founded on trust.
                </p>
              </div>

              {/* Pillar 2: Fairness */}
              <div className="flex flex-col items-center text-center p-6 border border-gray-100 rounded-xl shadow-lg">
                <div className="flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg">
                  <UserCheckIcon className="w-10 h-10" />
                </div>
                <h3 className="mt-6 text-2xl font-bold text-gray-900">
                  Adaptive Fairness Mode
                </h3>
                <p className="mt-4 text-lg text-gray-600">
                  We ensure our system is equitable and does not unfairly penalize students. At the start of an exam, the AI runs a brief calibration to assess factors like lighting and webcam quality. It then dynamically adjusts its sensitivity, preventing false positives and ensuring a fair experience for all students, regardless of their technical resources.
                </p>
              </div>
            </div>
          </div>
        </div>

      </main>

      <LandingFooter />
    </div>
  );
}

export default AboutUsPage;
