import React, { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import Header from "../components/Header";
import {
  AlertTriangle,
  Users,
  Bell,
  Send,
  XCircle,
  Activity,
} from "lucide-react";

const API_URL = "http://127.0.0.1:5000";

function LiveProctorDashboard() {
  const [user, setUser] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [proctorMessage, setProctorMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [stats, setStats] = useState({
    totalStudents: 0,
    highRisk: 0,
    mediumRisk: 0,
    totalAlerts: 0,
  });

  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const storedUser = JSON.parse(localStorage.getItem("proctorUser"));
    if (storedUser) {
      setUser(storedUser);
    }

    // Connect to WebSocket
    socketRef.current = io(API_URL, {
      transports: ["websocket"],
      reconnection: true,
    });

    socketRef.current.on("connect", () => {
      console.log("Connected to WebSocket");
      setConnected(true);
      // Join as proctor
      socketRef.current.emit("proctor_join", { proctor_id: storedUser?.id });
    });

    socketRef.current.on("disconnect", () => {
      console.log("Disconnected from WebSocket");
      setConnected(false);
    });

    // Listen for active sessions list
    socketRef.current.on("active_sessions_list", (data) => {
      setActiveSessions(data.sessions || []);
    });

    // Listen for new student joined
    socketRef.current.on("student_joined", (data) => {
      setActiveSessions((prev) => [...prev, data]);
      addMessage("system", `🟢 Student ${data.student_id} started exam`);
    });

    // Listen for new alerts
    socketRef.current.on("new_alert", (data) => {
      setActiveSessions((prev) =>
        prev.map((session) =>
          session.student_id === data.student_id
            ? {
                ...session,
                last_alert: { alert: data.alert, timestamp: data.timestamp },
                alert_count: data.alert_count,
                risk_level: data.risk_level,
                alerts_history: [
                  { alert: data.alert, timestamp: data.timestamp },
                  ...(session.alerts_history || []),
                ].slice(0, 10),
              }
            : session,
        ),
      );

      addMessage("alert", `⚠️ ${data.student_id}: ${data.alert}`);
      updateStats();
    });

    // Listen for student disconnected
    socketRef.current.on("student_disconnected", (data) => {
      setActiveSessions((prev) =>
        prev.filter((s) => s.student_id !== data.student_id),
      );
      addMessage("system", `🔴 Student ${data.student_id} left`);
    });

    // Listen for proctor warning confirmation
    socketRef.current.on("warning_sent", (data) => {
      addMessage("system", `✅ Warning sent to ${data.student_id}`);
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    updateStats();
  }, [activeSessions]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const updateStats = () => {
    setStats({
      totalStudents: activeSessions.length,
      highRisk: activeSessions.filter((s) => s.risk_level === "HIGH").length,
      mediumRisk: activeSessions.filter((s) => s.risk_level === "MEDIUM")
        .length,
      totalAlerts: activeSessions.reduce(
        (sum, s) => sum + (s.alert_count || 0),
        0,
      ),
    });
  };

  const addMessage = (type, text) => {
    setMessages((prev) => [
      ...prev,
      { type, text, timestamp: new Date().toLocaleTimeString() },
    ]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendWarning = () => {
    if (!selectedStudent || !proctorMessage.trim()) return;

    socketRef.current.emit("proctor_message", {
      student_id: selectedStudent.student_id,
      message: proctorMessage,
    });

    addMessage(
      "proctor",
      `📤 To ${selectedStudent.student_id}: ${proctorMessage}`,
    );
    setProctorMessage("");
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case "HIGH":
        return "bg-red-100 text-red-800 border-red-200";
      case "MEDIUM":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-green-100 text-green-800 border-green-200";
    }
  };

  const getRiskBadge = (risk) => {
    switch (risk) {
      case "HIGH":
        return "🔴 HIGH RISK";
      case "MEDIUM":
        return "🟡 MEDIUM RISK";
      default:
        return "🟢 LOW RISK";
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header username={user.username} portalType="Admin - Live Monitoring" />

      {/* Connection Status Bar */}
      <div
        className={`${connected ? "bg-green-500" : "bg-red-500"} text-white text-center py-1 text-sm transition-colors`}
      >
        {connected
          ? "🟢 Connected to Live Monitoring Server"
          : "🔴 Disconnected - Reconnecting..."}
      </div>

      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 flex items-center">
            <Users className="w-10 h-10 text-blue-500 mr-3" />
            <div>
              <p className="text-sm text-gray-500">Active Students</p>
              <p className="text-2xl font-bold">{stats.totalStudents}</p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 flex items-center">
            <AlertTriangle className="w-10 h-10 text-red-500 mr-3" />
            <div>
              <p className="text-sm text-gray-500">High Risk</p>
              <p className="text-2xl font-bold text-red-600">
                {stats.highRisk}
              </p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 flex items-center">
            <Activity className="w-10 h-10 text-yellow-500 mr-3" />
            <div>
              <p className="text-sm text-gray-500">Medium Risk</p>
              <p className="text-2xl font-bold text-yellow-600">
                {stats.mediumRisk}
              </p>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4 flex items-center">
            <Bell className="w-10 h-10 text-purple-500 mr-3" />
            <div>
              <p className="text-sm text-gray-500">Total Alerts</p>
              <p className="text-2xl font-bold">{stats.totalAlerts}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Active Sessions List */}
          <div className="lg:col-span-1 bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold flex items-center">
                <Users className="w-5 h-5 mr-2" />
                Active Sessions ({activeSessions.length})
              </h2>
            </div>
            <div className="divide-y max-h-[500px] overflow-y-auto">
              {activeSessions.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No active sessions
                </div>
              ) : (
                activeSessions.map((session) => (
                  <div
                    key={session.student_id}
                    onClick={() => setSelectedStudent(session)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition ${
                      selectedStudent?.student_id === session.student_id
                        ? "bg-indigo-50"
                        : ""
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium">{session.student_id}</span>
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(session.risk_level)}`}
                      >
                        {getRiskBadge(session.risk_level)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      <p>Exam: {session.exam_id}</p>
                      <p className="text-xs text-gray-400">
                        Started:{" "}
                        {new Date(session.joined_at).toLocaleTimeString()}
                      </p>
                      {session.last_alert && (
                        <p className="mt-1 text-xs text-red-600 truncate">
                          ⚠️ {session.last_alert.alert}
                        </p>
                      )}
                      <p className="mt-1 text-xs">
                        Alerts:{" "}
                        <span className="font-bold">
                          {session.alert_count || 0}
                        </span>
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Selected Student Details */}
          <div className="lg:col-span-2 space-y-4">
            {selectedStudent ? (
              <>
                {/* Student Info Card */}
                <div className="bg-white rounded-lg shadow p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h2 className="text-xl font-bold">
                        {selectedStudent.student_id}
                      </h2>
                      <p className="text-sm text-gray-600">
                        Session: {selectedStudent.session_id}
                      </p>
                      <p className="text-sm text-gray-600">
                        Exam ID: {selectedStudent.exam_id}
                      </p>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(selectedStudent.risk_level)}`}
                    >
                      {getRiskBadge(selectedStudent.risk_level)}
                    </span>
                  </div>

                  {/* Alert History */}
                  <div className="mt-4">
                    <h3 className="font-medium mb-2">Recent Alerts:</h3>
                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                      {selectedStudent.alerts_history?.map((alert, idx) => (
                        <div
                          key={idx}
                          className="bg-red-50 p-2 rounded text-sm border border-red-100"
                        >
                          <span className="text-red-800">⚠️ {alert.alert}</span>
                          <span className="text-xs text-gray-500 ml-2">
                            {new Date(alert.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                      {(!selectedStudent.alerts_history ||
                        selectedStudent.alerts_history.length === 0) && (
                        <p className="text-sm text-gray-500">No alerts yet</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Proctor Controls */}
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="font-medium mb-3">Proctor Controls</h3>
                  <div className="space-y-3">
                    <textarea
                      value={proctorMessage}
                      onChange={(e) => setProctorMessage(e.target.value)}
                      placeholder="Type warning message to student..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      rows="3"
                    />
                    <button
                      onClick={sendWarning}
                      disabled={!proctorMessage.trim()}
                      className="w-full flex items-center justify-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send Warning to Student
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <p className="text-lg">
                  Select a student from the list to monitor
                </p>
              </div>
            )}

            {/* Live Activity Feed */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-medium mb-3 flex items-center">
                <Activity className="w-4 h-4 mr-2" />
                Live Activity Feed
              </h3>
              <div className="h-[200px] overflow-y-auto bg-gray-50 rounded p-3">
                {messages.map((msg, idx) => (
                  <div key={idx} className="mb-2 text-sm">
                    <span className="text-gray-400 text-xs mr-2">
                      {msg.timestamp}
                    </span>
                    <span
                      className={
                        msg.type === "alert"
                          ? "text-red-600"
                          : msg.type === "system"
                            ? "text-blue-600"
                            : "text-indigo-600"
                      }
                    >
                      {msg.text}
                    </span>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveProctorDashboard;
