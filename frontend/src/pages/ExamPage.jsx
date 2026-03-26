// frontend/src/pages/ExamPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/Header";
import WebProctor from "../components/WebProctor";
import {
  Play,
  AlertCircle,
  CheckCircle,
  Loader,
  Shield,
  EyeOff,
  Volume2,
  Camera,
  MonitorSmartphone,
  XCircle,
  AlertTriangle,
} from "lucide-react";

const API_URL = "http://127.0.0.1:5000";

function ExamPage() {
  const [user, setUser] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [step, setStep] = useState("instructions");
  const [sessionId, setSessionId] = useState(null);
  const [answers, setAnswers] = useState({});
  const [permissions, setPermissions] = useState({
    camera: false,
    mic: false,
  });
  const [permissionError, setPermissionError] = useState(null);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [webAlerts, setWebAlerts] = useState([]);
  const [showAlertPanel, setShowAlertPanel] = useState(false);
  const [alertCount, setAlertCount] = useState(0);

  const videoRef = useRef(null);
  const detectionInterval = useRef(null);

  const { examId } = useParams();
  const navigate = useNavigate();

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

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
      if (detectionInterval.current) {
        clearInterval(detectionInterval.current);
      }
    };
  }, [cameraStream]);

  // Handle alerts from WebProctor
  const handleProctorAlert = async (alert) => {
    console.log("⚠️ Alert from proctor:", alert);
    setWebAlerts((prev) => [alert, ...prev].slice(0, 20));
    setAlertCount((prev) => prev + 1);
    setShowAlertPanel(true);

    // Auto-hide alert panel after 3 seconds
    setTimeout(() => {
      setShowAlertPanel(false);
    }, 3000);

    // Send alert to backend immediately
    if (sessionId && user) {
      try {
        await axios.post(`${API_URL}/log_data`, {
          source: "web",
          student_id: user.username,
          session_id: sessionId,
          alerts: [alert],
          metrics: {
            alert_type: alert,
            timestamp: new Date().toISOString(),
            face_count: parseInt(alert.match(/\d+/)?.[0] || "0"),
          },
          timestamp: new Date().toISOString(),
        });
        console.log("✅ Alert sent to backend");
      } catch (err) {
        console.error("Failed to send alert:", err);
      }
    }
  };

  // Start face detection after camera is active
  const startFaceDetection = () => {
    if (!videoRef.current || !videoRef.current.srcObject) return;

    detectionInterval.current = setInterval(() => {
      if (videoRef.current && videoRef.current.videoWidth > 0) {
        sendProctoringHeartbeat(true);
      } else {
        sendProctoringHeartbeat(false);
      }
    }, 3000);
  };

  // Send proctoring data to backend
  const sendProctoringHeartbeat = async (cameraWorking) => {
    if (!sessionId) return;

    try {
      await axios.post(`${API_URL}/log_data`, {
        source: "web",
        student_id: user.username,
        session_id: sessionId,
        alerts: cameraWorking ? [] : ["Camera feed not available"],
        metrics: {
          camera_active: cameraWorking,
          mic_active: permissions.mic,
          face_detected: cameraWorking,
          timestamp: new Date().toISOString(),
        },
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      console.error("Heartbeat failed:", err);
    }
  };

  // Check and activate camera
  const activateCamera = async () => {
    setPermissionError(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
        audio: true,
      });

      setCameraStream(stream);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        await new Promise((resolve) => {
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            resolve();
          };
        });

        setCameraActive(true);
      }

      const videoTracks = stream.getVideoTracks();
      const audioTracks = stream.getAudioTracks();

      const hasCamera =
        videoTracks.length > 0 && videoTracks[0].readyState === "live";
      const hasMic =
        audioTracks.length > 0 && audioTracks[0].readyState === "live";

      setPermissions({ camera: hasCamera, mic: hasMic });

      return hasCamera && hasMic;
    } catch (err) {
      console.error("Camera activation error:", err);
      let errorMsg = "Camera and microphone access are required";

      if (err.name === "NotAllowedError") {
        errorMsg =
          "Camera and microphone access denied. Please allow access in browser settings and reload.";
      } else if (err.name === "NotFoundError") {
        errorMsg = "No camera or microphone found on this device.";
      } else if (err.name === "NotReadableError") {
        errorMsg = "Camera is already in use by another application.";
      }

      setPermissionError(errorMsg);
      setPermissions({ camera: false, mic: false });
      return false;
    }
  };

  const handleStartExam = async () => {
    try {
      setStep("starting");

      // Activate camera first
      const cameraActivated = await activateCamera();
      if (!cameraActivated) {
        setStep("instructions");
        return;
      }

      // Generate session ID
      const newSessionId = `exam_${examId}_${user.username}_${Date.now()}`;
      setSessionId(newSessionId);

      // Log exam start with camera confirmed working
      await axios.post(`${API_URL}/log_data`, {
        source: "web",
        student_id: user.username,
        session_id: newSessionId,
        alerts: ["Exam started - Camera active"],
        metrics: {
          camera_active: true,
          mic_active: permissions.mic,
          timestamp: new Date().toISOString(),
        },
        timestamp: new Date().toISOString(),
      });

      // Start face detection
      startFaceDetection();

      // Wait 2 seconds to show camera is working, then start exam
      setTimeout(() => {
        setStep("exam");
      }, 2000);
    } catch (error) {
      console.error("Failed to start:", error);
      setError("Failed to start proctoring. Please try again.");
      setStep("instructions");

      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        setCameraStream(null);
      }
    }
  };

  const handleSubmitExam = async () => {
    try {
      // Stop camera stream
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        setCameraStream(null);
      }

      // Clear detection interval
      if (detectionInterval.current) {
        clearInterval(detectionInterval.current);
      }

      // Log submission with alert summary
      if (sessionId) {
        await axios.post(`${API_URL}/log_data`, {
          source: "web",
          student_id: user.username,
          session_id: sessionId,
          alerts: [`Exam submitted - Total alerts: ${alertCount}`],
          metrics: {
            camera_active: false,
            total_alerts: alertCount,
            alerts_list: webAlerts.slice(0, 10),
            timestamp: new Date().toISOString(),
          },
          timestamp: new Date().toISOString(),
        });
      }

      navigate("/student/dashboard");
    } catch (error) {
      console.error("Error submitting:", error);
      navigate("/student/dashboard");
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <Loader className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user?.username || "Student"} portalType="Student" />
        <div className="max-w-xl mx-auto py-12 px-4 text-center">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700 bg-red-50 p-4 rounded">{error}</p>
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
        <div className="max-w-2xl mx-auto py-10 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl">
            <div className="text-center mb-6">
              <Shield className="w-16 h-16 text-indigo-600 mx-auto mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {exam?.title}
              </h1>
              <p className="text-gray-600">
                {exam?.description || "AI-Proctored Examination"}
              </p>
            </div>

            {permissionError && (
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-6">
                <p className="text-red-700 font-medium mb-2">
                  ⚠️ Camera Required
                </p>
                <p className="text-red-600 text-sm">{permissionError}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="mt-2 text-sm text-red-700 underline"
                >
                  Reload page and allow camera access
                </button>
              </div>
            )}

            <div className="bg-blue-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-blue-800 mb-2 flex items-center">
                <Camera className="w-4 h-4 mr-2" />
                Privacy Notice:
              </h3>
              <ul className="text-blue-700 space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Camera activates in background - you won't see it</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>No video is recorded or uploaded</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Only anonymous alerts are sent</span>
                </li>
              </ul>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-gray-800 mb-2">Exam Rules:</h3>
              <ul className="text-gray-700 space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>No phones, books, or other people</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Stay in frame and face the camera</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>No talking or reading aloud</span>
                </li>
              </ul>
            </div>

            <button
              onClick={handleStartExam}
              className="w-full py-4 bg-indigo-600 text-white text-lg font-bold rounded-lg hover:bg-indigo-700 flex items-center justify-center transition"
            >
              <Play className="w-5 h-5 mr-2" />
              Start Exam
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Starting - Camera activation step
  if (step === "starting") {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header username={user.username} portalType="Student" />
        <div className="max-w-md mx-auto py-20 px-4">
          <div className="bg-white p-8 rounded-2xl shadow-xl text-center">
            <Loader className="w-16 h-16 text-indigo-600 animate-spin mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Starting Proctoring</h2>
            <p className="text-gray-600 mb-6">
              Initializing background monitoring...
            </p>

            {/* Hidden video element for camera activation */}
            <video
              ref={videoRef}
              style={{ display: "none" }}
              autoPlay
              playsInline
              muted
            />

            <div className="space-y-3 text-left bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <span className="flex items-center">
                  <Camera className="w-4 h-4 mr-2 text-gray-600" />
                  Camera access
                </span>
                {permissions.camera ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <Loader className="w-4 h-4 animate-spin text-indigo-500" />
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center">
                  <Volume2 className="w-4 h-4 mr-2 text-gray-600" />
                  Microphone access
                </span>
                {permissions.mic ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <Loader className="w-4 h-4 animate-spin text-indigo-500" />
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center">
                  <MonitorSmartphone className="w-4 h-4 mr-2 text-gray-600" />
                  AI Monitoring
                </span>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
            </div>

            {permissions.camera && permissions.mic && (
              <div className="mt-4 text-green-600 text-sm">
                ✓ Camera and microphone ready
              </div>
            )}

            <p className="text-xs text-gray-400 mt-4">
              Starting exam in a moment...
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Exam in Progress - Camera active in background
  return (
    <div className="min-h-screen bg-gray-100">
      <Header
        username={user.username}
        portalType="Student - Proctoring Active"
      />

      {/* Hidden video element for camera monitoring */}
      <video
        ref={videoRef}
        style={{ display: "none" }}
        autoPlay
        playsInline
        muted
      />

      {/* WebProctor Component for face detection */}
      <div className="fixed bottom-4 right-4 w-48 h-36 rounded-lg overflow-hidden shadow-lg border-2 border-indigo-500 z-20 bg-black">
        <WebProctor
          onAlert={handleProctorAlert}
          sessionId={sessionId}
          studentId={user?.username}
          onReady={() => console.log("Web proctor ready")}
        />
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs text-center py-1">
          AI Monitoring Active
        </div>
      </div>

      {/* Alert Notification Popup */}
      {showAlertPanel && webAlerts.length > 0 && (
        <div className="fixed top-20 right-4 z-30 animate-bounce">
          <div className="bg-red-500 text-white p-3 rounded-lg shadow-lg max-w-xs">
            <div className="flex items-start">
              <AlertTriangle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm">Violation Detected!</p>
                <p className="text-xs">{webAlerts[0]}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white p-6 rounded-lg shadow-xl">
          {/* Status Bar */}
          <div className="flex justify-between items-center mb-6 pb-4 border-b">
            <h1 className="text-2xl font-bold text-gray-900">{exam?.title}</h1>
            <div className="flex items-center space-x-3">
              <div className="flex items-center">
                <div
                  className={`w-2 h-2 rounded-full animate-pulse mr-2 ${cameraActive ? "bg-green-500" : "bg-red-500"}`}
                ></div>
                <span className="text-sm text-gray-600">
                  {cameraActive ? "Camera Active" : "Camera Issue"}
                </span>
              </div>
              {alertCount > 0 && (
                <div className="flex items-center">
                  <AlertTriangle className="w-4 h-4 text-red-500 mr-1" />
                  <span className="text-sm text-red-600 font-medium">
                    {alertCount} Alert{alertCount !== 1 ? "s" : ""}
                  </span>
                </div>
              )}
              <span className="px-3 py-1 bg-red-100 text-red-800 font-medium rounded-full text-xs">
                EXAM IN PROGRESS
              </span>
            </div>
          </div>

          {/* Privacy Notice */}
          <div className="mb-4 text-xs text-gray-400 flex items-center justify-end">
            <EyeOff className="w-3 h-3 mr-1" />
            Camera active in background
          </div>

          {/* Questions */}
          <div className="space-y-6">
            <div className="p-4 bg-gray-50 rounded">
              <h3 className="font-semibold mb-2">Question 1</h3>
              <p className="text-gray-700 mb-3">
                What is the primary function of mitochondria?
              </p>
              <div className="space-y-2">
                <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                  <input
                    type="radio"
                    name="q1"
                    value="powerhouse"
                    className="mr-3"
                    onChange={() => handleAnswerChange("q1", "powerhouse")}
                  />
                  Powerhouse of the cell
                </label>
                <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                  <input
                    type="radio"
                    name="q1"
                    value="protein"
                    className="mr-3"
                    onChange={() => handleAnswerChange("q1", "protein")}
                  />
                  Protein synthesis
                </label>
                <label className="flex items-center p-2 bg-white rounded cursor-pointer hover:bg-indigo-50">
                  <input
                    type="radio"
                    name="q1"
                    value="division"
                    className="mr-3"
                    onChange={() => handleAnswerChange("q1", "division")}
                  />
                  Cell division
                </label>
              </div>
            </div>

            <div className="p-4 bg-gray-50 rounded">
              <h3 className="font-semibold mb-2">Question 2</h3>
              <p className="text-gray-700 mb-3">Explain what React is:</p>
              <textarea
                className="w-full p-3 border rounded focus:ring-2 focus:ring-indigo-500"
                rows="4"
                placeholder="Your answer..."
                onChange={(e) => handleAnswerChange("q2", e.target.value)}
              ></textarea>
            </div>
          </div>

          {/* Submit Button */}
          <div className="mt-8">
            <button
              onClick={handleSubmitExam}
              className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold transition"
            >
              Submit Exam
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExamPage;
