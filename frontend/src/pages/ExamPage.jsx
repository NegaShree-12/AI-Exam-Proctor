import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import {
  Download,
  Play,
  AlertCircle,
  CheckCircle,
  Loader,
  Copy,
  Terminal,
  MonitorSmartphone,
  ExternalLink,
} from "lucide-react";

const API_URL = "http://127.0.0.1:5000";

function ExamPage() {
  const [user, setUser] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState("instructions"); // instructions, downloading, waiting, active, exam
  const [sessionToken, setSessionToken] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [clientStatus, setClientStatus] = useState("disconnected");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [clientCommand, setClientCommand] = useState("");
  const [clientFilename, setClientFilename] = useState("ProctorAI.exe");
  const [copySuccess, setCopySuccess] = useState(false);
  const [autoDetect, setAutoDetect] = useState(true);
  const [downloadAttempts, setDownloadAttempts] = useState(0);

  const { examId } = useParams();
  const navigate = useNavigate();
  const statusCheckInterval = useRef(null);
  const downloadInterval = useRef(null);

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem("proctorUser"));
    if (storedUser) {
      setUser(storedUser);
    } else {
      navigate("/login");
    }
  }, [navigate]);

  useEffect(() => {
    if (!examId || !user) return;

    const fetchExamDetails = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/api/exam_details/${examId}`,
        );
        setExam(response.data);
      } catch (err) {
        setError("Failed to load exam details");
      } finally {
        setLoading(false);
      }
    };

    fetchExamDetails();
  }, [examId, user]);

  // Cleanup intervals on unmount
  useEffect(() => {
    return () => {
      if (statusCheckInterval.current) {
        clearInterval(statusCheckInterval.current);
      }
      if (downloadInterval.current) {
        clearInterval(downloadInterval.current);
      }
    };
  }, []);

  const handleStartExam = async () => {
    try {
      setStep("downloading");

      // Request session from backend
      const response = await axios.post(`${API_URL}/api/start-client-session`, {
        username: user.username,
        exam_id: examId,
      });

      const {
        session_token,
        session_id,
        download_url,
        command,
        client_filename,
      } = response.data;

      setSessionToken(session_token);
      setSessionId(session_id);
      setDownloadUrl(download_url);
      setClientCommand(command);
      setClientFilename(client_filename);

      // Start download simulation
      simulateDownload();
    } catch (error) {
      console.error("Failed to start client session:", error);
      setError("Failed to start proctoring session. Please try again.");
      setStep("instructions");
    }
  };

  const simulateDownload = () => {
    let progress = 0;
    downloadInterval.current = setInterval(() => {
      progress += 10;
      setDownloadProgress(progress);

      if (progress >= 100) {
        clearInterval(downloadInterval.current);

        // Try to download the actual file
        downloadClientFile();

        // Move to waiting step
        setStep("waiting");
        startClientStatusCheck();
      }
    }, 300);
  };

  // 🔥 UPDATED: Improved download function with GitHub fallback
  const downloadClientFile = async () => {
    setDownloadAttempts((prev) => prev + 1);

    try {
      console.log(
        `Attempting to download: ${API_URL}/api/download-client/${clientFilename}`,
      );

      // Try to download from backend first
      const response = await fetch(
        `${API_URL}/api/download-client/${clientFilename}`,
        {
          method: "GET",
          headers: {
            Accept: "application/octet-stream",
          },
        },
      );

      if (response.redirected) {
        // If backend redirected to GitHub, open in new tab
        console.log("Redirected to:", response.url);
        window.open(response.url, "_blank");
      } else if (response.ok) {
        // Direct download from backend
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = clientFilename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        // Check if response is JSON (error message)
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const errorData = await response.json();
          console.log("Server returned error:", errorData);

          // Use the download_url from error if available
          if (errorData.download_url) {
            window.open(errorData.download_url, "_blank");
          } else {
            // Fallback to GitHub
            const githubUrl = `https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/${clientFilename}`;
            window.open(githubUrl, "_blank");
          }
        } else {
          // Fallback to GitHub
          const githubUrl = `https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/${clientFilename}`;
          window.open(githubUrl, "_blank");
        }
      }
    } catch (error) {
      console.error("Download failed:", error);

      // Ultimate fallback - try GitHub directly
      if (downloadAttempts < 3) {
        // Try one more time with a different approach
        setTimeout(() => {
          const githubUrl = `https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/${clientFilename}`;
          window.open(githubUrl, "_blank");
        }, 1000);
      } else {
        // Show manual download instructions
        alert(
          "Please download the client manually from:\n" +
            `https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/${clientFilename}`,
        );
      }
    }
  };

  const startClientStatusCheck = () => {
    // Start checking if client is running
    statusCheckInterval.current = setInterval(async () => {
      try {
        const response = await axios.get(
          `${API_URL}/api/check-client-status/${sessionToken}`,
        );

        if (response.data.status === "active") {
          setClientStatus("connected");
          setStep("active");
          clearInterval(statusCheckInterval.current);

          // Show success for 2 seconds then start exam
          setTimeout(() => {
            setStep("exam");
          }, 2000);
        }
      } catch (error) {
        // Client not connected yet, continue waiting
        console.log("Waiting for client to connect...");
      }
    }, 2000);
  };

  const copyCommandToClipboard = () => {
    navigator.clipboard.writeText(clientCommand);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const handleManualContinue = () => {
    // Skip waiting and go to exam (for testing)
    setStep("exam");
  };

  const handleSubmitExam = async () => {
    // Send final alert
    if (sessionId) {
      await axios.post(`${API_URL}/log_data`, {
        source: "web",
        student_id: user.username,
        session_id: sessionId,
        alerts: ["Exam submitted"],
        timestamp: new Date().toISOString(),
      });
    }

    navigate("/student/dashboard");
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-lg font-semibold text-indigo-600 animate-pulse">
          Loading Exam...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user?.username || "Student"} portalType="Student" />
        <div className="max-w-xl mx-auto py-12 px-4 text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-red-600 mb-4">⚠️ Error</h2>
          <p className="text-gray-700 bg-red-50 p-4 rounded border border-red-200">
            {error}
          </p>
          <button
            onClick={() => navigate("/student/dashboard")}
            className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Instructions Step
  if (step === "instructions") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user.username} portalType="Student" />
        <div className="max-w-4xl mx-auto py-10 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl space-y-6">
            {/* Exam Title */}
            <div className="text-center border-b pb-4">
              <h1 className="text-3xl font-extrabold text-gray-900">
                {exam?.title}
              </h1>
              {exam?.description && (
                <p className="mt-2 text-gray-600">{exam.description}</p>
              )}
            </div>

            {/* Rules Section */}
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-lg">
              <h2 className="text-xl font-bold text-yellow-800 mb-3">
                📜 Exam Rules
              </h2>
              <ul className="space-y-2 text-yellow-800">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>
                    <strong>AI Proctoring Active:</strong> Your session will be
                    monitored
                  </span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Be alone in a quiet room</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Keep face visible to webcam at all times</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>No phones, books, or other people</span>
                </li>
              </ul>
            </div>

            {/* One-Click Launch */}
            <div className="bg-green-50 border border-green-200 p-6 rounded-lg">
              <h2 className="text-xl font-bold text-green-800 mb-4 flex items-center">
                <MonitorSmartphone className="w-5 h-5 mr-2" />
                One-Click Launch
              </h2>

              <button
                onClick={handleStartExam}
                className="w-full py-4 bg-green-600 text-white text-lg font-bold rounded-lg hover:bg-green-700 transition flex items-center justify-center"
              >
                <Play className="w-5 h-5 mr-2" />
                Start Exam with AI Proctoring
              </button>

              <p className="text-sm text-green-600 mt-3 text-center">
                The proctoring agent will automatically download and launch
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Downloading Step
  if (step === "downloading") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user.username} portalType="Student" />
        <div className="max-w-md mx-auto py-20 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl text-center">
            <Loader className="w-16 h-16 text-blue-600 animate-spin mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">
              Preparing Proctoring Agent
            </h2>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${downloadProgress}%` }}
              ></div>
            </div>

            <p className="text-gray-600">{downloadProgress}% complete</p>

            <button
              onClick={downloadClientFile}
              className="mt-6 text-blue-600 hover:text-blue-800 text-sm"
            >
              Download manually instead
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Waiting for Client
  if (step === "waiting") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user.username} portalType="Student" />
        <div className="max-w-2xl mx-auto py-10 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-yellow-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Terminal className="w-10 h-10 text-yellow-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2">
                Launch the Proctoring Agent
              </h2>
              <p className="text-gray-600">
                The download should start automatically. If not, click below.
              </p>
            </div>

            {/* Download Button */}
            <div className="mb-6">
              <button
                onClick={downloadClientFile}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center justify-center"
              >
                <Download className="w-4 h-4 mr-2" />
                Download {clientFilename} Again
              </button>
            </div>

            {/* GitHub Direct Link */}
            <div className="mb-4 text-center">
              <a
                href={`https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/${clientFilename}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 flex items-center justify-center"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                Download directly from GitHub
              </a>
            </div>

            {/* Command to Run */}
            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                After downloading, run this command in terminal:
              </p>
              <div className="bg-gray-800 p-3 rounded flex items-center justify-between">
                <code className="text-green-300 text-sm font-mono select-all">
                  {clientCommand}
                </code>
                <button
                  onClick={copyCommandToClipboard}
                  className="ml-2 p-2 bg-gray-700 rounded hover:bg-gray-600 transition"
                >
                  {copySuccess ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-300" />
                  )}
                </button>
              </div>
            </div>

            {/* Status */}
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-2">
                Status:{" "}
                {clientStatus === "connected"
                  ? "✅ Connected"
                  : "⏳ Waiting for connection..."}
              </p>

              {autoDetect && (
                <p className="text-xs text-gray-400">
                  Auto-detecting client connection...
                </p>
              )}
            </div>

            {/* Manual override for testing */}
            <button
              onClick={handleManualContinue}
              className="mt-4 text-sm text-blue-600 hover:text-blue-800"
            >
              Continue to exam (for testing)
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Client Connected - Success
  if (step === "active") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user.username} portalType="Student" />
        <div className="max-w-md mx-auto py-20 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl text-center">
            <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-700 mb-2">
              Proctoring Agent Connected!
            </h2>
            <p className="text-gray-600 mb-6">
              Your exam session is now being monitored by AI
            </p>
            <div className="animate-pulse">
              <p className="text-sm text-gray-500">
                Starting exam in a moment...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Live Exam View
  if (step === "exam") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header
          username={user.username}
          portalType="Student - Proctoring Active"
        />
        <div className="max-w-5xl mx-auto py-8 px-4">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            {/* Header with Status */}
            <div className="flex justify-between items-center mb-6 pb-4 border-b">
              <h1 className="text-2xl font-bold text-gray-900">
                {exam?.title}
              </h1>
              <div className="flex items-center space-x-3">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
                  <span className="text-sm text-gray-600">AI Monitoring</span>
                </div>
                <span className="px-3 py-1 bg-red-100 text-red-800 font-medium rounded-full text-xs">
                  EXAM IN PROGRESS
                </span>
              </div>
            </div>

            {/* Session Info */}
            <div className="bg-gray-50 p-3 rounded mb-6 text-xs text-gray-500">
              Session ID: {sessionId}
            </div>

            {/* Exam Questions */}
            <div className="space-y-6">
              {/* Question 1 */}
              <div className="p-4 bg-gray-50 rounded">
                <h3 className="font-semibold mb-2">Question 1</h3>
                <p className="text-gray-700 mb-3">
                  What is the primary function of mitochondria?
                </p>
                <div className="space-y-2">
                  <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                    <input type="radio" name="q1" className="mr-3" />
                    Powerhouse of the cell
                  </label>
                  <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                    <input type="radio" name="q1" className="mr-3" />
                    Protein synthesis
                  </label>
                  <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                    <input type="radio" name="q1" className="mr-3" />
                    Cell division
                  </label>
                </div>
              </div>

              {/* Question 2 */}
              <div className="p-4 bg-gray-50 rounded">
                <h3 className="font-semibold mb-2">Question 2</h3>
                <p className="text-gray-700 mb-3">Explain what React is:</p>
                <textarea
                  className="w-full p-3 border rounded focus:ring-2 focus:ring-indigo-500"
                  rows="4"
                  placeholder="Your answer..."
                ></textarea>
              </div>
            </div>

            {/* Submit Button */}
            <div className="mt-8">
              <button
                onClick={handleSubmitExam}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold"
              >
                Submit Exam
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ExamPage;
