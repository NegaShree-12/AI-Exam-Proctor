import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ArrowLeft, Loader2 } from "lucide-react"; // Assuming lucide-react is installed

// Define the API URL for your backend
const API_URL = "http://127.0.0.1:5000";

// A helper for the social icon fallbacks (if needed later)
// const handleIconError = (e) => {
//   e.target.style.display = 'none'; // Hide broken icon
// };

function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    // Set view based on URL param, default to login
    setIsLogin(params.get("mode") !== "register");
  }, [location.search]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const endpoint = isLogin ? "/login" : "/register";
    const payload = isLogin
      ? { username, password }
      : { username, password, role };

    try {
      const response = await axios.post(`${API_URL}${endpoint}`, payload);
      if (isLogin) {
        const user = response.data.user;
        localStorage.setItem("proctorUser", JSON.stringify(user));
        navigate(
          user.role === "admin" ? "/admin/dashboard" : "/student/dashboard",
        );
      } else {
        setError("Registration successful! Please log in.");
        setIsLogin(true); // Switch to login view
        setPassword("");
        // Optionally clear username too, or keep it
        // setUsername('');
        // Navigate back to login mode visually
        navigate("/login", { replace: true });
      }
    } catch (err) {
      const message = err.response?.data?.message || "An error occurred.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Helper for switching views via buttons
  const setView = (view) => {
    const newIsLogin = view === "login";
    setIsLogin(newIsLogin);
    setError("");
    setUsername(""); // Clear fields on view switch
    setPassword("");
    // Update URL without full page reload
    navigate(newIsLogin ? "/login" : "/login?mode=register", { replace: true });
  };

  return (
    // Light gradient background matching Landing Page
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-white via-slate-50 to-gray-100 font-sans p-4">
      {/* "Back to Home" Link */}
      <Link
        to="/"
        className="absolute top-6 left-6 text-gray-600 hover:text-indigo-600 transition-colors duration-200 flex items-center group z-20"
      >
        <ArrowLeft className="w-5 h-5" />
        <span className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 font-medium text-sm">
          Back to Home
        </span>
      </Link>

      {/* Clean white card container */}
      <div className="bg-white shadow-xl rounded-2xl overflow-hidden flex flex-col md:flex-row w-full max-w-sm md:max-w-4xl min-h-[600px] md:min-h-[550px]">
        {/* Conditional Panels - Swapped Order for Login on Left */}
        {isLogin ? (
          <>
            {/* Left Section (Sign In Form) */}
            <FormPanel
              isLogin={true}
              username={username}
              setUsername={setUsername}
              password={password}
              setPassword={setPassword}
              role={role}
              setRole={setRole}
              handleSubmit={handleSubmit}
              error={error}
              loading={loading}
            />
            {/* Right Section (Sign Up CTA) */}
            <CTAPanel
              isLogin={false} // Show the opposite action ("New Here?")
              setView={setView}
            />
          </>
        ) : (
          <>
            {/* Left Section (Sign In CTA) */}
            <CTAPanel
              isLogin={true} // Show the opposite action ("Welcome Back!")
              setView={setView}
            />
            {/* Right Section (Sign Up Form) */}
            <FormPanel
              isLogin={false}
              username={username}
              setUsername={setUsername}
              password={password}
              setPassword={setPassword}
              role={role}
              setRole={setRole}
              handleSubmit={handleSubmit}
              error={error}
              loading={loading}
            />
          </>
        )}
      </div>
    </div>
  );
}

// --- Sub-components for clarity ---

/**
 * The panel containing the Sign In or Sign Up form.
 */
const FormPanel = ({
  isLogin,
  username,
  setUsername,
  password,
  setPassword,
  role,
  setRole,
  handleSubmit,
  error,
  loading,
}) => (
  <div className="w-full md:w-1/2 flex flex-col justify-center items-center px-8 sm:px-12 py-10 order-2 md:order-none">
    <div className="mb-6 text-center">
      <span className="text-3xl font-bold flex items-center justify-center">
        <span className="mr-2 text-3xl">🛡️</span>
        <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-800 to-indigo-900">
          ProctorAI+
        </span>
      </span>
    </div>

    <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
      {isLogin ? "Sign in" : "Create Account"}
    </h2>

    <form className="w-full max-w-xs space-y-5" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none focus:border-indigo-500 bg-gray-50 text-gray-700 transition duration-200"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none focus:border-indigo-500 bg-gray-50 text-gray-700 transition duration-200"
      />

      {!isLogin && (
        <select
          id="role"
          name="role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          required
          className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none focus:border-indigo-500 transition duration-200"
        >
          <option value="student">I am a Student</option>
          <option value="admin">I am an Admin/Creator</option>
        </select>
      )}

      {error && (
        <p className="text-sm text-center text-red-600 bg-red-50 p-2 rounded-md border border-red-200">
          {error}
        </p>
      )}

      {/* UPDATED: Button Styling to match new dark CTA Panel gradient */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-gradient-to-r from-blue-700 to-indigo-900 text-white rounded-lg font-semibold hover:from-blue-600 hover:to-indigo-800 transition-all flex justify-center items-center shadow-md hover:shadow-lg transform hover:-translate-y-0.5 disabled:from-blue-400 disabled:to-indigo-500 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-md"
      >
        {loading ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : isLogin ? (
          "SIGN IN"
        ) : (
          "SIGN UP"
        )}
      </button>
    </form>
  </div>
);

/**
 * The panel containing the "call to action".
 */
const CTAPanel = ({ isLogin, setView }) => (
  // NEW: Darker blue gradient background matching the image provided
  <div className="w-full md:w-1/2 bg-gradient-to-br from-blue-700 to-indigo-900 text-white flex flex-col justify-center items-center p-10 relative order-1 md:order-none min-h-[250px] md:min-h-full transition-all duration-300 ease-in-out">
    {" "}
    {/* Updated gradient */}
    <h2 className="text-3xl font-bold mb-3 text-center">
      {isLogin ? "Welcome Back!" : "New Here?"}
    </h2>
    <p className="text-center text-indigo-100 text-base mb-8 max-w-xs">
      {" "}
      {/* Lighter text for description */}
      {isLogin
        ? "Sign in to access your dashboard and manage your exams."
        : "Create an account to get started with secure, AI-powered proctoring."}
    </p>
    {/* Button styling remains suitable for dark background */}
    <button
      onClick={() => setView(isLogin ? "login" : "register")}
      className="border-2 border-white text-white px-8 py-2 rounded-full font-semibold hover:bg-white hover:text-indigo-700 transition-all duration-300 transform hover:scale-105 shadow-sm hover:shadow-md"
    >
      {isLogin ? "SIGN IN" : "SIGN UP"}
    </button>
  </div>
);

export default LoginPage;
