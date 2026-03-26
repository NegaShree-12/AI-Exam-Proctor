// frontend/src/components/WebProctor.jsx
import React, { useEffect, useRef, useState } from "react";
import * as tf from "@tensorflow/tfjs";
import * as faceDetection from "@tensorflow-models/face-detection";

function WebProctor({ onAlert, sessionId, studentId, onReady }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const detectorRef = useRef(null);
  const detectionActive = useRef(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [faceCount, setFaceCount] = useState(0);
  const alertInterval = useRef(null);

  useEffect(() => {
    initializeProctoring();
    return () => {
      detectionActive.current = false;
      if (alertInterval.current) {
        clearInterval(alertInterval.current);
      }
      if (videoRef.current?.srcObject) {
        videoRef.current.srcObject.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const initializeProctoring = async () => {
    try {
      // Initialize TensorFlow
      await tf.ready();
      console.log("✅ TensorFlow ready");

      // Initialize face detector
      const model = faceDetection.SupportedModels.MediaPipeFaceDetector;
      detectorRef.current = await faceDetection.createDetector(model, {
        runtime: "tfjs",
        maxFaces: 3,
      });
      console.log("✅ Face detector ready");

      // Start camera
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: 640,
          height: 480,
          facingMode: "user",
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        console.log("✅ Camera started");
        setIsInitialized(true);

        // Notify that proctoring is ready
        if (onReady) onReady();
      }

      // Start detection loop
      detectFaces();

      // Send periodic heartbeats with face data
      alertInterval.current = setInterval(sendProctoringData, 3000);
    } catch (error) {
      console.error("❌ Proctoring init failed:", error);
      setError(error.message);
      if (onAlert)
        onAlert("Proctoring initialization failed: " + error.message);
    }
  };

  const detectFaces = async () => {
    if (!detectorRef.current || !videoRef.current || !detectionActive.current)
      return;

    const detect = async () => {
      if (!detectionActive.current) return;

      try {
        const faces = await detectorRef.current.estimateFaces(videoRef.current);
        const currentFaceCount = faces.length;
        setFaceCount(currentFaceCount);

        // Draw on canvas
        if (canvasRef.current) {
          const ctx = canvasRef.current.getContext("2d");
          ctx.clearRect(
            0,
            0,
            canvasRef.current.width,
            canvasRef.current.height,
          );

          faces.forEach((face) => {
            const { x, y, width, height } = face.box;

            // Color code based on number of faces
            let color = "#10b981"; // Green for 1 face
            if (currentFaceCount > 1)
              color = "#ef4444"; // Red for multiple
            else if (currentFaceCount === 0) color = "#f59e0b"; // Orange for no face

            ctx.strokeStyle = color;
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, width, height);

            // Add label
            ctx.fillStyle = color;
            ctx.font = "bold 14px Arial";
            ctx.fillText("Face", x, y - 5);
          });

          // Add status text
          ctx.fillStyle = "#ffffff";
          ctx.font = "bold 16px Arial";
          ctx.shadowColor = "#000000";
          ctx.shadowBlur = 4;
          ctx.fillText(`Faces: ${currentFaceCount}`, 10, 30);
        }

        // Send alerts for violations
        if (currentFaceCount > 1) {
          if (onAlert) onAlert("⚠️ Multiple faces detected!");
        } else if (currentFaceCount === 0) {
          if (onAlert) onAlert("⚠️ No face detected!");
        }
      } catch (error) {
        console.error("Face detection error:", error);
      }

      if (detectionActive.current) {
        requestAnimationFrame(detect);
      }
    };

    detect();
  };

  const sendProctoringData = async () => {
    if (!sessionId || !studentId) return;

    // Generate alerts based on face detection
    const alerts = [];
    if (faceCount > 1) {
      alerts.push("Multiple faces detected!");
    }
    if (faceCount === 0) {
      alerts.push("No person detected!");
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/log_data", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: "web",
          student_id: studentId,
          session_id: sessionId,
          alerts: alerts,
          metrics: {
            face_count: faceCount,
            multiple_faces: faceCount > 1,
            no_face: faceCount === 0,
            timestamp: new Date().toISOString(),
          },
          timestamp: new Date().toISOString(),
        }),
      });

      if (alerts.length > 0) {
        console.log(`[Proctor] Sent alerts: ${alerts.join(", ")}`);
      }
    } catch (err) {
      console.error("Failed to send proctoring data:", err);
    }
  };

  if (error) {
    return (
      <div className="bg-red-100 text-red-700 p-4 rounded-lg">
        <p className="font-bold">Camera Error</p>
        <p className="text-sm">{error}</p>
        <p className="text-sm mt-2">Please ensure camera access is allowed</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        muted
        playsInline
      />
      <canvas
        ref={canvasRef}
        width={640}
        height={480}
        className="absolute inset-0 w-full h-full"
      />
      {!isInitialized && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <p>Initializing camera...</p>
          </div>
        </div>
      )}
      {/* Face count indicator */}
      {isInitialized && (
        <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs">
          Faces: {faceCount}
        </div>
      )}
    </div>
  );
}

export default WebProctor;
