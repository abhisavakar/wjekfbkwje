import { useState, useEffect, useRef } from "react";
import Head from "next/head";
import {
  Play,
  Square,
  Terminal,
  User,
  Bot,
  TrendingUp,
  Activity,
  BookOpen,
  GraduationCap,
} from "lucide-react";

export default function Dashboard() {
  const [status, setStatus] = useState("idle"); // idle, running, stopping
  const [logs, setLogs] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [estimates, setEstimates] = useState([]);
  const [currentLevel, setCurrentLevel] = useState(1);
  const [studentInfo, setStudentInfo] = useState({
    name: "Waiting...",
    topic: "-",
  });

  const logEndRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5000/api/stream");

    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);

      const timestamp = Date.now() / 1000;

      if (data.type === "start") {
        setLogs((prev) => [
          ...prev,
          {
            level: "success",
            message: `🚀 Agent started with set: ${data.data.set_type}`,
            timestamp,
          },
        ]);
      } else if (data.type === "session_start") {
        setStudentInfo({
          name: data.data.subject || "Student",
          topic: data.data.topic,
        });
        setChatHistory([]);
        setEstimates([]);
        setLogs((prev) => [
          ...prev,
          {
            level: "info",
            message: `📚 Starting session: ${data.data.topic}`,
            timestamp,
          },
        ]);
      } else if (data.type === "turn") {
        const { turn_number, tutor_message, student_response } = data.data;
        setChatHistory((prev) => [
          ...prev,
          { role: "tutor", content: tutor_message },
          { role: "student", content: student_response },
        ]);
        setLogs((prev) => [
          ...prev,
          {
            level: "info",
            message: `💬 Turn ${turn_number} completed`,
            timestamp,
          },
        ]);
      } else if (data.type === "level_estimate") {
        const { estimate, predicted_level } = data.data;
        setEstimates((prev) => [...prev, estimate]);
        setCurrentLevel(predicted_level);
        setLogs((prev) => [
          ...prev,
          {
            level: "info",
            message: `📊 Level estimate: ${estimate.toFixed(
              2
            )} → Predicted: ${predicted_level}`,
            timestamp,
          },
        ]);
      } else if (data.type === "session_complete") {
        const { topic, predicted_level, raw_estimate } = data.data;
        setLogs((prev) => [
          ...prev,
          {
            level: "success",
            message: `✅ Session complete: ${topic} | Final Level: ${predicted_level} (${raw_estimate.toFixed(
              2
            )})`,
            timestamp,
          },
        ]);
      } else if (data.type === "complete") {
        setLogs((prev) => [
          ...prev,
          {
            level: "success",
            message: `🎉 All sessions completed! Total predictions: ${data.data.predictions.length}`,
            timestamp,
          },
        ]);
        setStatus("idle");
      }
    };

    return () => eventSource.close();
  }, []);

  // Auto-scroll
  useEffect(
    () => logEndRef.current?.scrollIntoView({ behavior: "smooth" }),
    [logs]
  );
  useEffect(
    () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
    [chatHistory]
  );

  const toggleAgent = async () => {
    if (status === "idle") {
      setLogs([]);
      setChatHistory([]);
      setStatus("running");
      await fetch("http://localhost:5000/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ set_type: "mini_dev" }),
      });
    } else {
      setStatus("stopping");
      await fetch("http://localhost:5000/api/stop", { method: "POST" });
      setTimeout(() => setStatus("idle"), 1000);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F6F8] text-gray-800 font-sans flex flex-col">
      <Head>
        <title>Knowunity Agent Dashboard</title>
      </Head>

      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-[#12D18E] p-2 rounded-lg">
            <GraduationCap className="text-white" size={24} />
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight text-gray-900">
              Agent Olympics 2026
            </h1>
            <p className="text-xs text-gray-500 font-medium">
              REAL-TIME MONITORING DASHBOARD
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full">
            <div
              className={`w-2 h-2 rounded-full ${
                status === "running"
                  ? "bg-green-500 animate-pulse"
                  : "bg-gray-400"
              }`}
            />
            <span className="text-sm font-medium text-gray-600 uppercase">
              {status === "running" ? "Live Session" : "Standby"}
            </span>
          </div>

          <button
            onClick={toggleAgent}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-full font-bold text-white transition-all shadow-lg hover:shadow-xl active:scale-95 ${
              status === "running"
                ? "bg-red-500 hover:bg-red-600"
                : "bg-[#12D18E] hover:bg-[#0fb37a]"
            }`}
          >
            {status === "running" ? (
              <>
                <Square size={18} fill="currentColor" /> Stop Agent
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" /> Start Simulation
              </>
            )}
          </button>
        </div>
      </nav>

      <main className="flex-1 p-6 grid grid-cols-12 gap-6 max-h-[calc(100vh-80px)] overflow-hidden">
        {/* LEFT COLUMN: Student View (The "K12 App") */}
        <section className="col-span-12 lg:col-span-5 flex flex-col h-full">
          <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden flex flex-col h-full relative">
            {/* Phone Header */}
            <div className="bg-[#12D18E] p-6 text-white shrink-0">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold">{studentInfo.name}</h2>
                  <div className="flex items-center gap-2 opacity-90 mt-1">
                    <BookOpen size={16} />
                    <span className="font-medium">{studentInfo.topic}</span>
                  </div>
                </div>
                <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
                  <User size={24} />
                </div>
              </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#F0F2F5]">
              {chatHistory.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 gap-4">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
                    <Bot size={32} />
                  </div>
                  <p className="font-medium">Ready to start session...</p>
                </div>
              )}

              {chatHistory.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.role === "tutor" ? "justify-start" : "justify-end"
                  }`}
                >
                  {msg.role === "tutor" && (
                    <div className="w-8 h-8 rounded-full bg-[#12D18E] flex items-center justify-center text-white mr-2 shrink-0 mt-1">
                      <Bot size={16} />
                    </div>
                  )}

                  <div
                    className={`max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm text-[15px] leading-relaxed ${
                      msg.role === "tutor"
                        ? "bg-white text-gray-800 rounded-tl-none border border-gray-100"
                        : "bg-[#12D18E] text-white rounded-tr-none"
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Fake Input Area (Just for looks) */}
            <div className="p-4 bg-white border-t border-gray-100 shrink-0">
              <div className="h-12 bg-gray-100 rounded-full flex items-center px-6 text-gray-400 text-sm">
                AI is typing...
              </div>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN: Analytics & Developer Tools */}
        <section className="col-span-12 lg:col-span-7 grid grid-rows-2 gap-6 h-full">
          {/* Top Row: Metrics */}
          <div className="grid grid-cols-2 gap-6 h-full">
            {/* Level Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 flex flex-col relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                <TrendingUp size={120} />
              </div>
              <h3 className="text-gray-500 font-bold text-xs uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity size={14} /> Understanding Level
              </h3>

              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="text-7xl font-black text-[#12D18E] mb-2">
                  {currentLevel}
                  <span className="text-2xl text-gray-300 font-medium">/5</span>
                </div>
                <div className="flex gap-1.5 mt-4">
                  {[1, 2, 3, 4, 5].map((lvl) => (
                    <div
                      key={lvl}
                      className={`h-2 w-8 rounded-full transition-all duration-500 ${
                        lvl <= currentLevel ? "bg-[#12D18E]" : "bg-gray-100"
                      }`}
                    />
                  ))}
                </div>
                <p className="mt-4 text-sm font-medium text-gray-500 bg-gray-50 px-3 py-1 rounded-full">
                  {currentLevel === 1 && "Struggling / Needs Basics"}
                  {currentLevel === 2 && "Below Grade Level"}
                  {currentLevel === 3 && "At Grade Level"}
                  {currentLevel === 4 && "Above Grade / Concept Mastery"}
                  {currentLevel === 5 && "Advanced / Deep Understanding"}
                </p>
              </div>
            </div>

            {/* Confidence Graph (Simplified) */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 flex flex-col">
              <h3 className="text-gray-500 font-bold text-xs uppercase tracking-wider mb-4">
                Level Estimation History
              </h3>
              <div className="flex-1 flex items-end justify-between gap-1 px-2 border-b border-gray-100 pb-2">
                {estimates.length > 0 ? (
                  estimates.map((est, i) => (
                    <div
                      key={i}
                      className="flex flex-col items-center gap-1 w-full group"
                    >
                      <div
                        className="w-full bg-blue-500 rounded-t-md opacity-80 hover:opacity-100 transition-all relative"
                        style={{ height: `${(est / 5) * 100}%` }}
                      >
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                          {est.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300 text-sm">
                    No data points yet
                  </div>
                )}
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-2 font-mono">
                <span>Start</span>
                <span>Current Turn ({estimates.length})</span>
              </div>
            </div>
          </div>

          {/* Bottom Row: Logs (Terminal) */}
          <div className="bg-[#1E1E1E] rounded-2xl p-4 font-mono text-sm overflow-hidden flex flex-col shadow-lg border border-gray-800">
            <div className="flex items-center justify-between pb-2 border-b border-gray-800 mb-2">
              <div className="flex items-center gap-2 text-gray-400">
                <Terminal size={14} />
                <span className="text-xs font-bold uppercase">
                  System Output
                </span>
              </div>
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500/50" />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-1 pr-2 custom-scrollbar">
              {logs.length === 0 && (
                <span className="text-gray-600">System ready...</span>
              )}
              {logs.map((log, i) => (
                <div
                  key={i}
                  className="flex gap-3 text-xs leading-5 hover:bg-white/5 p-0.5 rounded"
                >
                  <span className="text-gray-500 shrink-0 w-16">
                    {new Date(log.timestamp * 1000).toLocaleTimeString([], {
                      hour12: false,
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                  <span
                    className={`${
                      log.level === "error"
                        ? "text-red-400 font-bold"
                        : log.level === "success"
                        ? "text-[#12D18E] font-bold"
                        : log.message.includes("Estimate")
                        ? "text-blue-300"
                        : "text-gray-300"
                    }`}
                  >
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
