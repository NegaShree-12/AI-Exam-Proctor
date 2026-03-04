import React, { useState, useEffect } from "react";
import axios from "axios";
import Header from "../components/Header";
import { Activity } from "lucide-react";
import AnalyticsDashboard from "../components/AnalyticsDashboard";

const API_URL = "http://127.0.0.1:5000";

function AdminDashboard() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("view_exams");

  // For 'View Exams'
  const [exams, setExams] = useState([]);
  const [loadingExams, setLoadingExams] = useState(false);

  // For 'Create Exam'
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loadingCreate, setLoadingCreate] = useState(false);

  // For 'Assign Exam'
  const [students, setStudents] = useState([]);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [assignExamId, setAssignExamId] = useState("");
  const [assignStudentId, setAssignStudentId] = useState("");
  const [loadingAssign, setLoadingAssign] = useState(false);

  // For 'View Sessions'
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [selectedExam, setSelectedExam] = useState(null);

  // For Analytics
  const [selectedSessionForAnalytics, setSelectedSessionForAnalytics] =
    useState(null);
  const [selectedExamForAnalytics, setSelectedExamForAnalytics] =
    useState(null);

  // General messages
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // --- Data Fetching Hooks ---

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem("proctorUser"));
    if (storedUser) {
      setUser(storedUser);
    }
    // Fetch exams on initial load
    fetchExams();
  }, []);

  useEffect(() => {
    // This effect runs when the 'view' state changes
    setError("");
    setSuccess("");

    if (view === "view_exams") {
      fetchExams();
    } else if (view === "assign_exam") {
      if (exams.length === 0) fetchExams();
      if (students.length === 0) fetchStudents();
    } else if (view === "view_sessions" && selectedExam) {
      fetchSessions(selectedExam.id);
    }
  }, [view, selectedExam]);

  // --- API Functions ---

  const fetchExams = async () => {
    setLoadingExams(true);
    try {
      const response = await axios.get(`${API_URL}/api/exams`);
      setExams(response.data);
      if (response.data.length > 0 && !assignExamId) {
        setAssignExamId(response.data[0].id);
      }
    } catch (err) {
      setError("Failed to fetch exams.");
    } finally {
      setLoadingExams(false);
    }
  };

  const fetchStudents = async () => {
    setLoadingStudents(true);
    try {
      const response = await axios.get(`${API_URL}/api/students`);
      setStudents(response.data);
      if (response.data.length > 0 && !assignStudentId) {
        setAssignStudentId(response.data[0].id);
      }
    } catch (err) {
      setError("Failed to fetch students.");
    } finally {
      setLoadingStudents(false);
    }
  };

  const fetchSessions = async (examId) => {
    setLoadingSessions(true);
    try {
      const response = await axios.get(
        `${API_URL}/api/exam_sessions/${examId}`,
      );
      setSessions(response.data);
    } catch (err) {
      setError("Failed to fetch proctoring sessions.");
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleCreateExam = async (e) => {
    e.preventDefault();
    if (!user) return;
    setLoadingCreate(true);
    setSuccess("");
    setError("");
    try {
      const payload = { title, description, admin_id: user.id };
      await axios.post(`${API_URL}/api/exams`, payload);
      setSuccess("Exam created successfully!");
      setTitle("");
      setDescription("");
      changeView("view_exams");
    } catch (err) {
      setError(err.response?.data?.message || "Failed to create exam.");
    } finally {
      setLoadingCreate(false);
    }
  };

  const handleAssignExam = async (e) => {
    e.preventDefault();
    if (!assignExamId || !assignStudentId) {
      setError("Please select both an exam and a student.");
      return;
    }
    setLoadingAssign(true);
    setSuccess("");
    setError("");
    try {
      const payload = { exam_id: assignExamId, student_id: assignStudentId };
      await axios.post(`${API_URL}/api/assign`, payload);
      setSuccess("Exam assigned successfully!");
    } catch (err) {
      setError(err.response?.data?.message || "Failed to assign exam.");
    } finally {
      setLoadingAssign(false);
    }
  };

  // --- UI Control Functions ---

  const changeView = (newView) => {
    setView(newView);
    if (newView !== "view_sessions") {
      setSelectedExam(null);
    }
  };

  const handleViewSessions = (exam) => {
    setSelectedExam(exam);
    changeView("view_sessions");
  };

  const handleViewExamAnalytics = (exam) => {
    setSelectedExamForAnalytics(exam);
  };

  // --- Render Logic ---

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header username={user.username} portalType="Admin" />

      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Navigation Tabs */}
        {view !== "view_sessions" && (
          <div className="mb-6">
            <nav className="flex space-x-4" aria-label="Tabs">
              <button
                onClick={() => changeView("view_exams")}
                className={`px-4 py-2 font-medium rounded-md text-sm ${
                  view === "view_exams"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-gray-600 bg-white hover:bg-gray-50"
                }`}
              >
                View Exams
              </button>
              <button
                onClick={() => changeView("create_exam")}
                className={`px-4 py-2 font-medium rounded-md text-sm ${
                  view === "create_exam"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-gray-600 bg-white hover:bg-gray-50"
                }`}
              >
                Create New Exam
              </button>
              <button
                onClick={() => changeView("assign_exam")}
                className={`px-4 py-2 font-medium rounded-md text-sm ${
                  view === "assign_exam"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-gray-600 bg-white hover:bg-gray-50"
                }`}
              >
                Assign Exam
              </button>
              <button
                onClick={() => (window.location.href = "/admin/live")}
                className="px-4 py-2 font-medium rounded-md text-sm bg-green-500 text-white hover:bg-green-600 shadow-sm flex items-center"
              >
                <Activity className="w-4 h-4 mr-1" />
                LIVE MONITORING
              </button>
            </nav>
          </div>
        )}

        {/* Success/Error Messages */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded-md">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 border border-green-200 rounded-md">
            {success}
          </div>
        )}

        {/* --- View Exams Content --- */}
        {view === "view_exams" && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">All Exams</h2>
            {loadingExams ? (
              <p>Loading exams...</p>
            ) : (
              <div className="space-y-4">
                {exams.length === 0 ? (
                  <p>No exams created yet.</p>
                ) : (
                  exams.map((exam) => (
                    <div
                      key={exam.id}
                      className="p-4 border border-gray-200 rounded-lg flex justify-between items-center transition-shadow hover:shadow-lg"
                    >
                      <div>
                        <h3 className="text-lg font-semibold text-indigo-700">
                          {exam.title}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {exam.description || "No description"}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Created by: {exam.admin_username} on{" "}
                          {new Date(exam.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleViewSessions(exam)}
                          className="px-3 py-2 bg-indigo-100 text-indigo-700 text-sm font-medium rounded-md hover:bg-indigo-200"
                        >
                          View Sessions
                        </button>
                        <button
                          onClick={() => handleViewExamAnalytics(exam)}
                          className="px-3 py-2 bg-purple-100 text-purple-700 text-sm font-medium rounded-md hover:bg-purple-200"
                        >
                          Analytics
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        )}

        {/* --- Create Exam Content --- */}
        {view === "create_exam" && (
          <div className="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">
              Create a New Exam
            </h2>
            <form onSubmit={handleCreateExam} className="space-y-4">
              <div>
                <label
                  htmlFor="title"
                  className="block text-sm font-medium text-gray-700"
                >
                  Exam Title
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700"
                >
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  rows="3"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <button
                  type="submit"
                  disabled={loadingCreate}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
                >
                  {loadingCreate ? "Creating..." : "Create Exam"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- Assign Exam Content --- */}
        {view === "assign_exam" && (
          <div className="bg-white p-6 rounded-lg shadow-md max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">
              Assign Exam to Student
            </h2>
            <form onSubmit={handleAssignExam} className="space-y-4">
              <div>
                <label
                  htmlFor="exam"
                  className="block text-sm font-medium text-gray-700"
                >
                  Select Exam
                </label>
                <select
                  id="exam"
                  value={assignExamId}
                  onChange={(e) => setAssignExamId(e.target.value)}
                  disabled={loadingExams}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {exams.map((exam) => (
                    <option key={exam.id} value={exam.id}>
                      {exam.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="student"
                  className="block text-sm font-medium text-gray-700"
                >
                  Select Student
                </label>
                <select
                  id="student"
                  value={assignStudentId}
                  onChange={(e) => setAssignStudentId(e.target.value)}
                  disabled={loadingStudents}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {students.map((student) => (
                    <option key={student.id} value={student.id}>
                      {student.username}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <button
                  type="submit"
                  disabled={loadingAssign}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400"
                >
                  {loadingAssign ? "Assigning..." : "Assign Exam"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* --- View Sessions Content --- */}
        {view === "view_sessions" && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div>
                <button
                  onClick={() => changeView("view_exams")}
                  className="mb-2 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  &larr; Back to All Exams
                </button>
                <h2 className="text-2xl font-bold text-gray-800">
                  Proctoring Sessions for:{" "}
                  <span className="text-indigo-700">{selectedExam?.title}</span>
                </h2>
              </div>
            </div>

            {loadingSessions ? (
              <p>Loading sessions...</p>
            ) : (
              <div className="space-y-4">
                {sessions.length === 0 ? (
                  <p>
                    No proctoring sessions have been recorded for this exam yet.
                  </p>
                ) : (
                  sessions.map((session) => {
                    const reportUrl = `${API_URL}/generate_report/${session.student_username}/${session.session_id}`;

                    return (
                      <div
                        key={session.session_id}
                        className="p-4 border border-gray-200 rounded-lg flex flex-col sm:flex-row justify-between sm:items-center"
                      >
                        <div className="mb-3 sm:mb-0">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {session.student_username}
                          </h3>
                          <p className="text-sm text-gray-600">
                            Started on:{" "}
                            {new Date(session.start_time).toLocaleString()}
                          </p>
                          <p className="text-sm text-gray-600">
                            Final Score:{" "}
                            <span className="font-bold">
                              {session.final_score} / 100
                            </span>
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <a
                            href={reportUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-2 bg-green-500 text-white text-sm font-medium rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 text-center"
                          >
                            Download Report
                          </a>
                          <button
                            onClick={() =>
                              setSelectedSessionForAnalytics(session)
                            }
                            className="px-3 py-2 bg-blue-500 text-white text-sm font-medium rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            View Analytics
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Session Analytics Modal */}
      {selectedSessionForAnalytics && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <AnalyticsDashboard
              sessionId={selectedSessionForAnalytics.session_id}
              onClose={() => setSelectedSessionForAnalytics(null)}
            />
          </div>
        </div>
      )}

      {/* Exam Analytics Modal */}
      {selectedExamForAnalytics && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <AnalyticsDashboard
              examId={selectedExamForAnalytics.id}
              onClose={() => setSelectedExamForAnalytics(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
