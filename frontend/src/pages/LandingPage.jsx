import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck, UsersRound, ScanSearch, Hand, ListChecks, UserPlus, FilePlus, Play, FileDown,
  BrainCircuit, SlidersHorizontal, MousePointerClick, ChevronLeft, ChevronRight
} from 'lucide-react';

// --- Header Component (Unchanged) ---
const LandingHeader = () => {
  return (
    <nav className="bg-white/90 backdrop-blur-lg shadow-sm border-b border-gray-200/50 sticky top-0 z-50 w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          <Link to="/" className="flex items-center gap-2 group">
             <span className="text-3xl font-bold flex items-center">
               <span className="mr-2 text-3xl group-hover:scale-110 transition-transform duration-300">🛡️</span>
              {/* Darker Blue Gradient Title */}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-800 to-indigo-900">
                ProctorAI+
              </span>
            </span>
          </Link>
          <div className="flex items-center space-x-8">
            <div className="hidden md:flex items-center space-x-6">
              <Link
                to="/about"
                className="text-lg font-medium text-gray-600 hover:text-indigo-600 transition-colors duration-200"
              >
                About Us
              </Link>
              <a
                href="#features"
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-lg font-medium text-gray-600 hover:text-indigo-600 transition-colors duration-200"
              >
                Features
              </a>
               <a
                href="#how-to-use"
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById('how-to-use')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="text-lg font-medium text-gray-600 hover:text-indigo-600 transition-colors duration-200"
              >
                How to Use
              </a>
            </div>
            <div className="flex items-center space-x-3">
              <Link
                to="/login"
                className="text-lg font-medium text-indigo-600 hover:text-indigo-800 transition-colors duration-200 px-4 py-2 rounded-lg hover:bg-indigo-50"
              >
                Login
              </Link>
              <Link
                to="/login?mode=register"
                className="text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200 px-5 py-2 rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              >
                Sign Up
              </Link>
            </div>
             <div className="md:hidden">
               {/* Mobile Menu Button Placeholder */}
             </div>
          </div>
        </div>
      </div>
    </nav>
  );
};


// --- Footer Component (Unchanged) ---
const LandingFooter = () => {
  return (
    <footer className="bg-gray-900 border-t border-gray-700 py-6 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-400">
        <p className="text-sm">
           <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">🛡️ ProctorAI+</span> &copy; {new Date().getFullYear()}. All rights reserved.
        </p>
      </div>
    </footer>
  );
};


// --- Main Landing Page Component ---
function LandingPage() {

    // Scroll animations effect (Unchanged)
    useEffect(() => {
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-section-in');
                    entry.target.classList.remove('opacity-0', 'translate-y-10');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.section-animate').forEach(el => {
            el.classList.add('opacity-0', 'translate-y-10', 'transition-all', 'duration-1000', 'ease-out');
            sectionObserver.observe(el);
        });

    // Trigger hero animation for all hero-animate elements immediately
    document.querySelectorAll('.hero-animate').forEach(el => {
      el.classList.add('animate-hero-in');
      el.classList.remove('opacity-0', 'translate-y-8', 'scale-95');
    });

        // Cleanup observers
        return () => {
             sectionObserver.disconnect();
        };
    }, []);


  return (
     <>
       {/* Inject animation styles (Unchanged) */}
       <style>
        {`
          @keyframes section-in {
             from { opacity: 0; transform: translateY(40px); }
             to { opacity: 1; transform: translateY(0); }
           }
           .animate-section-in {
              animation: section-in 1s ease-out forwards;
           }
           @keyframes hero-in {
             0% { opacity: 0; transform: translateY(30px) scale(0.95); }
             100% { opacity: 1; transform: translateY(0) scale(1); }
           }
            .animate-hero-in {
               animation: hero-in 0.8s ease-out forwards;
            }

            /* Slideshow step animation - Fade */
            @keyframes step-fade-in {
              from { opacity: 0; }
              to { opacity: 1; }
            }
             @keyframes step-fade-out {
              from { opacity: 1; }
              to { opacity: 0; }
            }

            .slide-item {
              transition: opacity 0.5s ease-in-out;
              position: absolute;
              top: 0;
              left: 0;
              width: 100%;
              opacity: 0; /* Hidden by default */
              pointer-events: none; /* Prevent interaction when hidden */
            }
            .slide-item.active {
              opacity: 1;
              position: relative; /* Take up space */
              pointer-events: auto;
              animation: step-fade-in 0.5s ease-in-out forwards;
            }
            .slide-item.exiting {
                 animation: step-fade-out 0.5s ease-in-out forwards;
                 pointer-events: none;
             }
        `}
      </style>

      {/* Light background (Unchanged) */}
      <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-gray-100 text-gray-800 font-sans">
        <LandingHeader />

        {/* Hero Section */}
        <section className="py-24 sm:py-32 overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-12">

            {/* MODIFIED: Left Side - Text Content */}
            <div className="md:w-1/2 lg:w-7/12 text-center md:text-left hero-animate opacity-0 transform translate-y-8 scale-95 md:order-1">
              {/* REMOVED Logo Image from here */}
              {/* <img src="https://placehold.co/100x100/..." /> */}

               {/* Title block - Now stands alone */}
               <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-gray-900 leading-tight mb-6"> {/* Added mb-6 */}
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-800 to-indigo-900">
                      ProctorAI+
                  </span>
                  <span className="block text-gray-800 mt-1 text-4xl sm:text-5xl lg:text-6xl">
                      Secure AI Proctoring
                  </span>
               </h1>

              {/* Description and Buttons remain below */}
              <p className="text-xl text-gray-600 max-w-xl mx-auto md:mx-0 mb-8">
                A next-generation, AI-powered exam proctoring system with a privacy-first philosophy.
                Ensure academic integrity while respecting student privacy.
              </p>
              <div className="flex flex-col sm:flex-row justify-center md:justify-start space-y-4 sm:space-y-0 sm:space-x-4">
                <Link
                  to="/login?mode=register"
                  className="text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200 px-8 py-3 rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5 inline-block text-center" > Get Started </Link>
                <a
                  href="#features"
                  onClick={(e) => { e.preventDefault(); document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' }); }}
                  className="text-lg font-medium text-indigo-600 hover:text-indigo-800 transition-colors duration-200 px-8 py-3 rounded-lg hover:bg-indigo-50 border border-indigo-200 inline-block text-center" > Learn More </a>
              </div>
            </div>

        {/* MODIFIED: Right Side - Placeholder Image */}
        <div className="md:w-1/2 lg:w-5/12 flex justify-center hero-animate opacity-0 transform translate-y-8 scale-95 md:order-2" style={{ animationDelay: '200ms' }}>
          <img
            src="/image.png" /* Served from Vite/CRA public root */
            alt="AI Proctoring Illustration"
            className="rounded-lg shadow-xl object-cover w-full h-auto max-w-[560px]" /* constrain width */
            onError={(e) => { e.target.src = 'https://placehold.co/600x400/eeeeee/aaaaaa?text=Image+Error'; }}
           />
        </div>

          </div>
        </section>

        {/* Features Section (Unchanged) */}
        <section id="features" className="py-20 bg-white section-animate">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-4xl font-bold text-center text-gray-900 mb-16">
              Why Choose ProctorAI+?
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
               <FeatureCard icon={UsersRound} iconBg="bg-indigo-100" iconColor="text-indigo-600" title="Dual Attention Model" description="Correlates head pose with voice activity to reduce false positives." />
               <FeatureCard icon={ScanSearch} iconBg="bg-purple-100" iconColor="text-purple-600" title="Environment Detection" description="Uses AI to detect unauthorized objects like phones, books, or extra people." />
               <FeatureCard icon={Hand} iconBg="bg-teal-100" iconColor="text-teal-600" title="Micro Gesture Analysis" description="Tracks subtle hand movements suggesting hidden earpieces or devices." />
               <FeatureCard icon={BrainCircuit} iconBg="bg-rose-100" iconColor="text-rose-600" title="Cognitive Load Meter" description="Estimates student stress and confusion via blink rate and facial expressions." />
               <FeatureCard icon={SlidersHorizontal} iconBg="bg-amber-100" iconColor="text-amber-600" title="Adaptive Fairness Mode" description="Adjusts AI sensitivity based on lighting and webcam quality for equity." />
               <FeatureCard icon={MousePointerClick} iconBg="bg-sky-100" iconColor="text-sky-600" title="Web-Based Monitoring" description="Detects tab-switching and browser focus loss directly in the web portal." />
            </div>
          </div>
        </section>


        {/* How to Use Section (Unchanged) */}
        <section id="how-to-use" className="py-20 bg-gradient-to-br from-white via-slate-50 to-gray-100 section-animate">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
             <h2 className="text-4xl font-bold text-center text-gray-900 mb-10">
               How to Use the Platform
             </h2>
             <HowToSlideshow />
          </div>
        </section>

        <LandingFooter />
      </div>
    </>
  );
}

// --- Helper Components ---

// Feature Card (Unchanged)
const FeatureCard = ({ icon: Icon, iconBg, iconColor, title, description }) => (
   <div className="text-center p-6 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-lg transition-shadow duration-300 transform hover:-translate-y-1 flex flex-col items-center">
    <div className={`flex justify-center mb-5 p-4 rounded-full ${iconBg}`}>
       <Icon className={`w-8 h-8 ${iconColor}`} />
    </div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-gray-600 text-base">{description}</p>
  </div>
);

// Data for the steps (Unchanged)
const stepsData = [
  { number: 1, icon: UserPlus, title: "Log In / Register", description: "Log in with the provided demo credentials as Admin or Student to explore the system." },
  { number: 2, icon: FilePlus, title: "Create & Assign (Admin)", description: "The Admin can create new exams, define questions, and manage settings, then assign the exam to a student." },
  { number: 3, icon: Play, title: "Start Exam (Student)", description: "The Student signs in, opens their dashboard, and starts the assigned exam when ready. (Remember to run the AI agent!)" },
  { number: 4, icon: ShieldCheck, title: "AI Monitoring", description: "During the exam, the AI monitoring system actively analyzes the session in the background to ensure integrity." },
  { number: 5, icon: ListChecks, title: "Review Session (Admin)", description: "After submission, the Admin can review detailed session records, including behavior analysis and flagged alerts." },
  { number: 6, icon: FileDown, title: "Download Report (Admin)", description: "A PDF report is available for download to evaluate performance and proctoring results." }
];

// How To Slideshow Component (Unchanged logic)
const HowToSlideshow = () => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const intervalRef = useRef(null);
  const timeoutRef = useRef(null);

  const totalSteps = stepsData.length;

  const goToStep = (index) => {
      if (timeoutRef.current || index === currentStepIndex) return;

      setIsExiting(true);
       timeoutRef.current = setTimeout(() => {
           setCurrentStepIndex(index);
           setIsExiting(false);
            timeoutRef.current = null;
           resetInterval();
        }, 500);
  };

  const goToNext = () => {
    const nextIndex = (currentStepIndex + 1) % totalSteps;
    goToStep(nextIndex);
  };

  const goToPrevious = () => {
    const prevIndex = (currentStepIndex - 1 + totalSteps) % totalSteps;
    goToStep(prevIndex);
  };

   const resetInterval = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
     timeoutRef.current = null;
    intervalRef.current = setInterval(goToNext, 5000);
  };

  useEffect(() => {
     resetInterval();
     return () => {
         if (intervalRef.current) clearInterval(intervalRef.current);
         if (timeoutRef.current) clearTimeout(timeoutRef.current);
     };
  }, []);


  return (
    <div className="relative">
      {/* Slides Container */}
       <div className="relative min-h-[250px] sm:min-h-[200px] overflow-hidden mb-6">
          {stepsData.map((step, index) => (
            <div
                key={step.number}
                className={`slide-item ${index === currentStepIndex && !isExiting ? 'active' : ''} ${index === currentStepIndex && isExiting ? 'exiting' : ''}`}
            >
              {/* Dark blue gradient card */}
              <div className="bg-gradient-to-br from-blue-800 to-indigo-900 text-white rounded-2xl shadow-xl p-8 sm:p-10">
                 <HowToStepItem isVisible={index === currentStepIndex && !isExiting} {...step} />
              </div>
            </div>
          ))}
       </div>

      {/* Navigation Buttons */}
      <div className="flex justify-center items-center gap-4 mt-8">
        <button
          onClick={goToPrevious}
          className="p-3 rounded-full bg-indigo-500 hover:bg-indigo-600 text-white transition-colors disabled:opacity-50 shadow-md"
          aria-label="Previous Step"
          disabled={isExiting}
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
         {/* Dots Indicator */}
         <div className="flex gap-2">
           {stepsData.map((_, index) => (
             <button
               key={index}
               onClick={() => {
                   if (index !== currentStepIndex) {
                       goToStep(index);
                   }
               }}
               className={`w-3 h-3 rounded-full transition-colors ${
                 index === currentStepIndex ? 'bg-indigo-600' : 'bg-gray-300 hover:bg-gray-400'
               }`}
               aria-label={`Go to step ${index + 1}`}
               disabled={isExiting}
             />
           ))}
         </div>
        <button
          onClick={goToNext}
          className="p-3 rounded-full bg-indigo-500 hover:bg-indigo-600 text-white transition-colors disabled:opacity-50 shadow-md"
          aria-label="Next Step"
          disabled={isExiting}
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};


// Step Item Component (Unchanged)
const HowToStepItem = ({ icon: Icon, title, description, isVisible }) => (
  <div className={`flex items-start gap-4 sm:gap-6 transition-opacity duration-500 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
    <div className="flex-grow pt-1">
      <h3 className="text-xl sm:text-2xl font-semibold mb-2 flex items-center gap-3 text-white">
        <Icon className="w-7 h-7 text-indigo-300 flex-shrink-0" />
        {title}
      </h3>
      <p className="text-indigo-100 text-base sm:text-lg min-h-[6em] sm:min-h-[4.5em]">{description || ''} {(!description || description.length < 50) && '\u00A0'}</p>
    </div>
  </div>
);

export default LandingPage;

