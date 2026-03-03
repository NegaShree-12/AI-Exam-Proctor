# AI-Exam-Proctor

**AI-Exam-Proctor** is a sophisticated, AI-powered online examination proctoring system developed with a strong emphasis on privacy and fairness. Unlike traditional proctoring services that stream sensitive user data to external servers, this system processes all video and audio feeds locally on the student's machine, ensuring that personal data never leaves their device.

The system employs a multi-layered approach to integrity monitoring, combining computer vision, object detection, and voice analysis to create a comprehensive picture of the test-taking environment. Only anonymized alert data is transmitted to the administrative dashboard, striking a perfect balance between security and privacy.

This repository contains the complete full-stack implementation including the React-based web portal, Flask backend API, and the Python-based AI proctoring agent.

---

## 👨‍💻 About The Developer

This project was developed by **NEGA** as a demonstration of advanced full-stack development skills combined with cutting-edge AI/ML integration. The system showcases expertise in:

- **Frontend Development**: React with modern hooks and responsive design
- **Backend Engineering**: RESTful API design with Flask and SQLite
- **Computer Vision**: Real-time face detection and object recognition
- **Machine Learning Integration**: YOLOv8 and MediaPipe implementation
- **System Architecture**: Edge computing principles with local processing

---

## ✨ Core Features

### 🔍 Intelligent Proctoring Agent (Python Client)

The heart of the system is a sophisticated Python-based agent that runs on the student's local machine:

- **Multi-Face Detection**: Utilizes OpenCV's advanced cascade classifiers to detect if more than one person is present in the frame, preventing impersonation and unauthorized assistance.

- **Object Detection with YOLOv8**: Employs state-of-the-art YOLOv8 model to identify prohibited items in real-time:
  - 📱 Mobile phones and smart devices
  - 💻 Laptops and secondary screens
  - 📚 Open books and study materials
  - 📝 Notes and cheat sheets

- **Voice Activity Detection**: Continuous audio monitoring that detects:
  - Multiple voices/conversations in the room
  - Reading aloud or dictation
  - External audio sources
  - Speech-to-text transcription for suspicious keywords

- **Adaptive Fairness System**: Automatically calibrates detection sensitivity based on:
  - Ambient lighting conditions
  - Webcam quality and resolution
  - Background noise levels
  Ensures students aren't unfairly penalized for technical limitations.

- **Real-time Alert Generation**: Instantly flags violations and maintains a rolling buffer of recent events for context.

### 🌐 Web Portal (React Frontend)

A modern, responsive web application built with React and Tailwind CSS:

**For Administrators:**
- **Secure Authentication**: Role-based login system separating admin and student access
- **Exam Management Dashboard**: Create, edit, and manage examination details
- **Student Assignment Interface**: Assign specific exams to registered students
- **Live Monitoring Panel**: Real-time view of active exam sessions
- **Comprehensive Review System**: Browse completed sessions with detailed violation logs
- **Automated Report Generation**: Download detailed PDF reports for each session

**For Students:**
- **Personalized Dashboard**: View only assigned exams
- **Guided Exam Flow**: Step-by-step instructions for launching the proctoring agent
- **Real-time Status Indicators**: Visual feedback on proctoring status
- **Session History**: Access to past exam results and reports

### ⚙️ Backend API (Flask)

A robust Python Flask backend handling all server-side operations:

- **User Authentication**: Secure password hashing and session management
- **Exam CRUD Operations**: Create, read, and manage examination data
- **Assignment Tracking**: Database relations for exam-student assignments
- **Event Logging**: Centralized endpoint for all proctoring events
- **Report Generation**: Dynamic PDF creation with violation timelines
- **Data Export**: CSV export functionality for further analysis

---

## 🛠️ Technology Stack

### Frontend
- **React 18** with Hooks and Functional Components
- **Vite** for fast development and optimized builds
- **Tailwind CSS** for responsive, utility-first styling
- **React Router DOM** for seamless navigation
- **Axios** for API integration
- **Lucide React** for beautiful, consistent icons

### Backend
- **Flask** lightweight Python web framework
- **SQLite** for embedded, zero-configuration database
- **Flask-CORS** for secure cross-origin requests
- **Flask-SocketIO** for real-time communication
- **Werkzeug** for password hashing and security
- **Pandas** for data manipulation and exports

### AI/ML Components
- **OpenCV** for real-time video processing
- **YOLOv8** (Ultralytics) for object detection
- **MediaPipe** for face landmark detection
- **SpeechRecognition** for voice-to-text conversion
- **PyTorch** backend for YOLO models
- **NumPy** for numerical operations

### Development & Deployment
- **Git** for version control
- **PyInstaller** for creating standalone executables
- **npm/yarn** for dependency management
- **Vercel/Netlify** ready for frontend deployment

---

## 📁 Project Structure
AI-Exam-Proctor/
├── backend/ # Flask backend application
│ ├── app.py # Main application entry point
│ ├── analytics_engine.py # Data analysis and reporting
│ ├── report_generator.py # PDF report generation
│ ├── websocket_manager.py # Real-time communication
│ ├── requirements.txt # Python dependencies
│ └── venv/ # Virtual environment (local)
│
├── client-agent/ # Python proctoring agent
│ ├── main.py # Agent entry point
│ └── requirements.txt # Agent dependencies
│
├── frontend/ # React web application
│ ├── src/
│ │ ├── components/ # Reusable UI components
│ │ ├── pages/ # Page components
│ │ ├── services/ # API service modules
│ │ ├── App.jsx # Main application
│ │ └── main.jsx # Entry point
│ ├── public/ # Static assets
│ ├── package.json # Node dependencies
│ └── node_modules/ # Local node packages
│
├── .gitignore # Git ignore rules
└── README.md # Project documentation

text

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **pip** (Python package manager)
- **npm** or **yarn** (Node package manager)
- **Git** (for version control)
- **Webcam and Microphone** (for testing the proctoring agent)

### Step 1: Clone the Repository
```bash
git clone https://github.com/NEGA/AI-Exam-Proctor.git
cd AI-Exam-Proctor
Step 2: Backend Setup
bash
cd backend

# Create and activate virtual environment
# On Windows:
python -m venv venv
venv\Scripts\activate

# On Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
The backend server will start at http://127.0.0.1:5000

Step 3: Frontend Setup
bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
The frontend application will be available at http://localhost:5173

Step 4: Test the Proctoring Agent
bash
# Open a third terminal
cd client-agent

# Create and activate virtual environment
python -m venv venv
# Activate as shown above

# Install dependencies
pip install -r requirements.txt

# Run the agent (replace with your test credentials)
python main.py --username test_student --exam_id 1
📖 Usage Guide
For Administrators
Registration: Create an admin account at /login?mode=register

Create Exam: Navigate to Admin Dashboard → "Create New Exam"

Add Students: View all registered students in the dashboard

Assign Exams: Select an exam and assign it to students

Monitor Live: Watch active sessions in real-time

Review Results: Browse completed sessions and download reports

For Students
Registration: Create a student account

View Exams: Check your dashboard for assigned exams

Start Exam: Click "Start Exam" on any pending exam

Launch Agent: Follow the on-screen instructions to run the proctoring agent

Complete Exam: Answer questions while being monitored

Submit: Review and submit your answers

🔒 Privacy & Security
AI-Exam-Proctor prioritizes user privacy through several key design decisions:

Edge Processing: All video and audio processing occurs locally on the student's machine. Raw footage is never transmitted or stored.

Minimal Data Transmission: Only anonymized alert data (e.g., "Multiple faces detected at 14:32:15") is sent to the server.

Secure Authentication: Passwords are hashed using industry-standard algorithms before storage.

Session Isolation: Each exam session generates unique identifiers, preventing cross-session data leakage.

Automatic Cleanup: Temporary files and reports are automatically deleted after download.

🧪 Testing the System
Test Credentials
text
Admin Account:
- Username: admin
- Password: admin123

Student Account:
- Username: student1
- Password: student123
Test Scenarios
Single User Test: Run the agent alone and verify normal operation

Multiple Faces: Have someone enter the frame and observe detection

Object Detection: Show a phone or book to the camera

Voice Test: Speak loudly and check voice detection

Tab Switching: Switch browser tabs during the exam

⚠️ Known Limitations
YOLO Model Size: The initial download of YOLOv8 model (~6MB) occurs on first run

Python Dependency: Students must have Python installed (or use the compiled executable)

Browser Support: Requires modern browsers with WebRTC support

Resource Usage: AI processing can be CPU-intensive on older machines

Internet Dependency: Requires stable internet for server communication

🔮 Future Enhancements
Browser-Based Detection: Migrate all AI processing to TensorFlow.js for zero-installation

Mobile App: Native iOS/Android applications for tablet-based exams

Advanced Analytics: Machine learning models to detect suspicious patterns across sessions

Video Recording: Optional secure recording storage for manual review

Cheat Pattern Detection: AI models to identify common cheating behaviors

Integration APIs: REST APIs for integration with popular LMS platforms

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

📞 Contact & Support
Developer: NEGA
Project Link: https://github.com/NEGA/AI-Exam-Proctor

For support, please open an issue in the GitHub repository or contact the developer directly.

🙏 Acknowledgments
OpenCV community for computer vision libraries

Ultralytics for YOLOv8 implementation

React and Flask communities for excellent documentation

All contributors and testers who helped refine the system

© 2025 AI-Exam-Proctor by NEGA. All rights reserved.