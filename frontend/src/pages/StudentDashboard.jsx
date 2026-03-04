import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";

const API_URL = "http://127.0.0.1:5000";

function StudentDashboard() {
  const [user, setUser] = useState(null);
  const [assignedExams, setAssignedExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem("proctorUser"));
    if (storedUser) {
      setUser(storedUser);
      fetchMyExams(storedUser.id);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchMyExams = async (studentId) => {
    setLoading(true);
    setError("");
    try {
      const response = await axios.get(`${API_URL}/api/my_exams/${studentId}`);
      setAssignedExams(response.data);
    } catch (err) {
      setError("Failed to fetch your assigned exams.");
    } finally {
      setLoading(false);
    }
  };

  const handleStartExam = (examId) => {
    // Navigate to the exam page, passing the exam ID in the URL
    navigate(`/exam/${examId}`);
  };

  if (!user) {
    // This check is good, but ProtectedRoute should prevent this
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header username={user.username} portalType="Student" />

      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4 text-gray-800">
            My Assigned Exams
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          {loading ? (
            <p>Loading exams...</p>
          ) : (
            <div className="space-y-4">
              {assignedExams.length === 0 ? (
                <p className="text-gray-600">
                  You have no exams assigned to you at this time.
                </p>
              ) : (
                assignedExams.map((exam) => (
                  <div
                    key={exam.exam_id}
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
                        Assigned on:{" "}
                        {new Date(exam.assigned_at).toLocaleDateString()}
                      </p>
                    </div>
                    {/* We'll add logic for 'completed' status later */}
                    <button
                      onClick={() => handleStartExam(exam.exam_id)}
                      className="px-4 py-2 bg-green-500 text-white text-sm font-medium rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                    >
                      Start Exam
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default StudentDashboard;
