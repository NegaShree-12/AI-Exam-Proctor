import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ComposedChart,
  Scatter,
} from "recharts";
import {
  Download,
  Calendar,
  TrendingUp,
  AlertTriangle,
  Users,
  Clock,
  Award,
} from "lucide-react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import * as FileSaver from "file-saver";

const API_URL = "http://127.0.0.1:5000";

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
];

function AnalyticsDashboard({ examId, sessionId, onClose }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [viewType, setViewType] = useState(sessionId ? "session" : "exam");
  const [dateRange, setDateRange] = useState([null, null]);
  const [startDate, endDate] = dateRange;

  useEffect(() => {
    fetchAnalytics();
  }, [examId, sessionId]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      let endpoint = sessionId
        ? `${API_URL}/api/analytics/session/${sessionId}`
        : `${API_URL}/api/analytics/exam/${examId}`;

      const response = await axios.get(endpoint);
      setAnalytics(response.data);
    } catch (err) {
      setError("Failed to fetch analytics data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/api/export/${viewType}/${sessionId || examId}`,
        { responseType: "blob" },
      );
      FileSaver.saveAs(
        response.data,
        `${viewType}_analytics_${Date.now()}.csv`,
      );
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return <div className="bg-red-50 p-4 rounded-lg text-red-700">{error}</div>;
  }

  if (!analytics) {
    return (
      <div className="bg-yellow-50 p-4 rounded-lg text-yellow-700">
        No analytics data available
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            {viewType === "session" ? "Session Analytics" : "Exam Analytics"}
          </h2>
          <p className="text-sm text-gray-600">
            {viewType === "session"
              ? `Session ID: ${sessionId}`
              : `Exam ID: ${examId}`}
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={exportToCSV}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {viewType === "session" ? (
          // Session level cards
          <>
            <SummaryCard
              icon={<Award className="w-8 h-8 text-blue-500" />}
              title="Final Score"
              value={`${analytics.integrity_stats?.final_score || 0}/100`}
              color="blue"
            />
            <SummaryCard
              icon={<Clock className="w-8 h-8 text-green-500" />}
              title="Duration"
              value={`${analytics.duration || 0} min`}
              color="green"
            />
            <SummaryCard
              icon={<AlertTriangle className="w-8 h-8 text-red-500" />}
              title="Total Alerts"
              value={analytics.summary?.total_alerts || 0}
              color="red"
            />
            <SummaryCard
              icon={<TrendingUp className="w-8 h-8 text-purple-500" />}
              title="Alert Rate"
              value={`${analytics.alert_frequency || 0}/min`}
              color="purple"
            />
          </>
        ) : (
          // Exam level cards
          <>
            <SummaryCard
              icon={<Users className="w-8 h-8 text-blue-500" />}
              title="Total Students"
              value={analytics.total_sessions || 0}
              color="blue"
            />
            <SummaryCard
              icon={<Award className="w-8 h-8 text-green-500" />}
              title="Avg Score"
              value={`${analytics.avg_integrity_score?.toFixed(1) || 0}/100`}
              color="green"
            />
            <SummaryCard
              icon={<AlertTriangle className="w-8 h-8 text-red-500" />}
              title="Total Alerts"
              value={analytics.total_alerts || 0}
              color="red"
            />
            <SummaryCard
              icon={<Clock className="w-8 h-8 text-purple-500" />}
              title="Avg Duration"
              value={`${analytics.avg_duration?.toFixed(1) || 0} min`}
              color="purple"
            />
          </>
        )}
      </div>

      {/* Risk Distribution */}
      {viewType === "session" && analytics.risk_distribution && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    {
                      name: "Low Risk",
                      value: analytics.risk_distribution.low,
                    },
                    {
                      name: "Medium Risk",
                      value: analytics.risk_distribution.medium,
                    },
                    {
                      name: "High Risk",
                      value: analytics.risk_distribution.high,
                    },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  <Cell fill="#4CAF50" />
                  <Cell fill="#FFC107" />
                  <Cell fill="#F44336" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Score Timeline */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Score Timeline</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics.score_timeline?.slice(-20)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#8884d8"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Alert Distribution */}
      {analytics.unique_alerts && analytics.unique_alerts.length > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg mb-8">
          <h3 className="text-lg font-semibold mb-4">Alert Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analytics.unique_alerts.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="alert"
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8">
                {analytics.unique_alerts.slice(0, 10).map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Exam Level Charts */}
      {viewType === "exam" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {analytics.score_distribution && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Score Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.score_distribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {analytics.performance_groups && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Performance Groups</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      {
                        name: "Excellent (90+)",
                        value: analytics.performance_groups.excellent,
                      },
                      {
                        name: "Good (80-90)",
                        value: analytics.performance_groups.good,
                      },
                      {
                        name: "Fair (70-80)",
                        value: analytics.performance_groups.fair,
                      },
                      {
                        name: "Poor (<70)",
                        value: analytics.performance_groups.poor,
                      },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    <Cell fill="#4CAF50" />
                    <Cell fill="#8BC34A" />
                    <Cell fill="#FFC107" />
                    <Cell fill="#F44336" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Peak Risk Times */}
      {analytics.peak_risk_times && analytics.peak_risk_times.length > 0 && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">Peak Risk Times</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {analytics.peak_risk_times.map((peak, index) => (
              <div
                key={index}
                className="bg-red-50 p-4 rounded-lg border border-red-200"
              >
                <p className="text-sm text-red-600">Time: {peak.time}</p>
                <p className="text-lg font-bold text-red-700">
                  Score: {peak.avg_score}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Summary Card Component
function SummaryCard({ icon, title, value, color }) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-700",
    green: "bg-green-50 text-green-700",
    red: "bg-red-50 text-red-700",
    purple: "bg-purple-50 text-purple-700",
  };

  return (
    <div className={`p-4 rounded-lg ${colorClasses[color]}`}>
      <div className="flex items-center">
        {icon}
        <div className="ml-3">
          <p className="text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold">{value}</p>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
