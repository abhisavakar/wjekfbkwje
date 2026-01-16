"use client";

import { useState, useEffect, useRef } from "react";
import {
  Play,
  Square,
  Terminal,
  User,
  Bot,
  Activity,
  Award,
  BarChart3,
  Zap,
  RefreshCw,
  Trophy,
} from "lucide-react";
import {
  AgentStatus,
  LogMessage,
  ChatMessage,
  LevelEstimate,
  StudentInfo,
} from "../types";

export default function Dashboard() {
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [estimates, setEstimates] = useState<LevelEstimate[]>([]);
  const [currentLevel, setCurrentLevel] = useState<number>(0);
  const [currentConfidence, setCurrentConfidence] = useState<number>(0);
  const [studentInfo, setStudentInfo] = useState<StudentInfo>({
    name: "Ready",
    topic: "Waiting to start...",
  });
  const [finalScores, setFinalScores] = useState<{
    mse: string | null;
    tutoring: string | null;
  }>({ mse: null, tutoring: null });

  const logEndRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Derived state for Visual Clamping (Prevents UI from showing inflated scores)
  const displayLevel = (() => {
    // Safety: If level is high (>4) but confidence is low (<50%), visually dampen it
    if (currentLevel > 4.0 && currentConfidence < 0.5) return 3.5;
    return currentLevel;
  })();

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5000/api/stream");

    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === "log") {
        const logData = data as LogMessage;
        // Limit logs to last 100 to prevent DOM lag
        setLogs((prev) => [...prev.slice(-99), logData]);

        if (logData.message.includes("Processing")) {
          const match = logData.message.match(/Processing (.*?) - (.*)/);
          if (match) {
            setStudentInfo({ name: match[1], topic: match[2] });
            setChatHistory([]);
            setEstimates([]);
            setCurrentLevel(0);
            setCurrentConfidence(0);
            setFinalScores({ mse: null, tutoring: null }); // Reset scores on new student
          }
        }

        if (logData.message.includes("FINAL_MSE_SCORE:")) {
          setFinalScores((prev) => ({
            ...prev,
            mse: logData.message.split(":")[1].trim(),
          }));
        }
        if (logData.message.includes("FINAL_TUTORING_SCORE:")) {
          setFinalScores((prev) => ({
            ...prev,
            tutoring: logData.message.split(":")[1].trim(),
          }));
        }
      } else if (data.type === "state_update") {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const stateData = data as any;
        setChatHistory(stateData.history);
        setEstimates(stateData.estimates);
        setCurrentLevel(stateData.current_level);
        setCurrentConfidence(stateData.current_confidence);
      }
    };

    return () => eventSource.close();
  }, []);

  // Smart Auto-scroll
  useEffect(() => {
    if (logs.length > 0)
      logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  useEffect(() => {
    if (chatHistory.length > 0)
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const toggleAgent = async () => {
    if (status === "idle") {
      setStatus("running");
      setLogs([]);
      setFinalScores({ mse: null, tutoring: null });
      try {
        await fetch("http://localhost:5000/api/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ set_type: "mini_dev" }),
        });
      } catch (error) {
        console.error("Failed to start agent:", error);
        setStatus("idle");
      }
    } else {
      setStatus("stopping");
      try {
        await fetch("http://localhost:5000/api/stop", { method: "POST" });
      } catch (e) {
        console.error(e);
      }
      setTimeout(() => setStatus("idle"), 1000);
    }
  };

  return (
    <div className="h-screen bg-gray-50 text-gray-900 font-sans flex flex-col overflow-hidden">
      {/* Header - Fixed Height */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shrink-0 shadow-sm z-20">
        <div className="flex items-center gap-3">
          <div className="bg-knowunity-green p-2 rounded-lg text-white">
            <Zap size={20} fill="currentColor" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight text-gray-900">
              Knowunity Tutor Agent
            </h1>
            <p className="text-xs text-gray-500 font-medium">
              LIVE MONITORING DASHBOARD
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Live Score Ticker */}
          {(finalScores.mse || finalScores.tutoring) && (
            <div className="flex gap-4 mr-4 animate-in fade-in slide-in-from-top-4 duration-500">
              <div className="px-4 py-1.5 bg-blue-50 border border-blue-200 rounded-lg flex flex-col items-center shadow-sm">
                <span className="text-[10px] font-bold text-blue-500 uppercase tracking-wide">
                  MSE Score
                </span>
                <span className="font-mono font-bold text-blue-700">
                  {finalScores.mse ? Number(finalScores.mse).toFixed(4) : "..."}
                </span>
              </div>
              <div className="px-4 py-1.5 bg-purple-50 border border-purple-200 rounded-lg flex flex-col items-center shadow-sm">
                <span className="text-[10px] font-bold text-purple-500 uppercase tracking-wide">
                  Tutoring Score
                </span>
                <span className="font-mono font-bold text-purple-700">
                  {finalScores.tutoring || "-"}/5
                </span>
              </div>
            </div>
          )}

          <div
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide flex items-center gap-2 transition-colors ${
              status === "running"
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${
                status === "running"
                  ? "bg-green-500 animate-pulse"
                  : "bg-gray-400"
              }`}
            ></div>
            {status === "running" ? "Active" : "Idle"}
          </div>
          <button
            onClick={toggleAgent}
            className={`flex items-center gap-2 px-5 py-2 rounded-lg font-semibold text-sm transition-all text-white shadow-sm hover:shadow-md active:scale-95 ${
              status === "running"
                ? "bg-red-500 hover:bg-red-600"
                : "bg-knowunity-green hover:bg-knowunity-dark"
            }`}
          >
            {status === "running" ? (
              <>
                <Square size={16} fill="currentColor" /> Stop Session
              </>
            ) : (
              <>
                <Play size={16} fill="currentColor" /> Start Evaluation
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Content - Flex Grow */}
      <main className="flex-1 p-6 grid grid-cols-12 gap-6 min-h-0">
        {/* LEFT: Live Conversation */}
        <section className="col-span-12 lg:col-span-7 flex flex-col bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-full">
          <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center text-knowunity-dark font-bold text-lg border border-green-200">
                {studentInfo.name[0]}
              </div>
              <div>
                <h2 className="font-bold text-sm text-gray-900">
                  {studentInfo.name}
                </h2>
                <p className="text-xs text-gray-500 font-medium">
                  {studentInfo.topic}
                </p>
              </div>
            </div>
            <div className="text-xs font-mono text-gray-400 bg-white px-2 py-1 rounded border border-gray-100">
              Turn {Math.floor(chatHistory.length / 2)}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-6 bg-white scroll-smooth">
            {chatHistory.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-gray-300 gap-3">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center">
                  <RefreshCw
                    size={32}
                    className={status === "running" ? "animate-spin" : ""}
                  />
                </div>
                <p className="text-sm font-medium">
                  Waiting for active session...
                </p>
              </div>
            )}
            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${
                  msg.role === "tutor" ? "flex-row-reverse" : ""
                } animate-in fade-in slide-in-from-bottom-2 duration-300`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border ${
                    msg.role === "tutor"
                      ? "bg-knowunity-green text-white border-transparent"
                      : "bg-gray-100 text-gray-500 border-gray-200"
                  }`}
                >
                  {msg.role === "tutor" ? (
                    <Bot size={16} />
                  ) : (
                    <User size={16} />
                  )}
                </div>
                <div
                  className={`max-w-[85%] p-3.5 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    msg.role === "tutor"
                      ? "bg-knowunity-green text-white rounded-tr-none"
                      : "bg-gray-50 text-gray-800 rounded-tl-none border border-gray-100"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </section>

        {/* RIGHT: Metrics & Logs */}
        <section className="col-span-12 lg:col-span-5 flex flex-col gap-6 h-full min-h-0">
          {/* Metric Cards */}
          <div className="grid grid-cols-2 gap-4 shrink-0">
            {/* Level Card */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200 relative overflow-hidden group">
              <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                <Award size={14} /> Predicted Level
              </div>
              <div className="flex items-end gap-2">
                <span className="text-5xl font-black text-gray-900">
                  {displayLevel > 0 ? displayLevel.toFixed(1) : "-"}
                </span>
                <span className="text-gray-400 font-medium mb-1">/ 5.0</span>
              </div>
              <div className="mt-4 h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-knowunity-green transition-all duration-700 ease-out"
                  style={{ width: `${(displayLevel / 5) * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Confidence Card */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-200">
              <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
                <Activity size={14} /> AI Confidence
              </div>
              <div className="flex items-end gap-2">
                <span
                  className={`text-5xl font-black ${
                    currentConfidence > 0.8
                      ? "text-green-500"
                      : currentConfidence > 0.5
                      ? "text-yellow-500"
                      : "text-gray-900"
                  }`}
                >
                  {(currentConfidence * 100).toFixed(0)}
                </span>
                <span className="text-gray-400 font-medium mb-1">%</span>
              </div>
              <div className="mt-4 h-2 w-full bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ease-out ${
                    currentConfidence > 0.8
                      ? "bg-green-500"
                      : currentConfidence > 0.5
                      ? "bg-yellow-500"
                      : "bg-gray-400"
                  }`}
                  style={{ width: `${currentConfidence * 100}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Charts Area */}
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 shrink-0 flex flex-col h-40">
            <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">
              <BarChart3 size={14} /> Level Progression
            </div>
            <div className="flex-1 flex items-end gap-1.5 w-full">
              {estimates.length === 0 && (
                <div className="w-full h-full flex items-center justify-center text-xs text-gray-300 border-2 border-dashed border-gray-100 rounded-lg">
                  Waiting for data...
                </div>
              )}
              {estimates.map((est, i) => (
                <div
                  key={i}
                  className="flex-1 flex flex-col justify-end gap-1 group relative h-full"
                >
                  <div
                    className="w-full bg-blue-500 rounded-t-sm opacity-80 hover:opacity-100 transition-all duration-500"
                    style={{ height: `${Math.max(5, (est.level / 5) * 100)}%` }}
                  ></div>
                  <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none transition-opacity">
                    Turn {i + 1}: {est.level.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Terminal Logs */}
          <div className="bg-[#1E1E1E] rounded-xl p-4 flex-1 overflow-hidden flex flex-col shadow-inner border border-gray-800 min-h-0">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2 mb-2 shrink-0">
              <div className="flex items-center gap-2 text-gray-400 text-xs font-bold uppercase">
                <Terminal size={12} /> System Kernel
              </div>
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
                <div className="w-2 h-2 rounded-full bg-green-500/50"></div>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-2 font-mono text-[11px] custom-scrollbar">
              {logs.map((log, i) => (
                <div
                  key={i}
                  className="flex gap-3 hover:bg-white/5 p-0.5 rounded transition-colors"
                >
                  <span className="text-gray-600 shrink-0 select-none">
                    {new Date(log.timestamp * 1000).toLocaleTimeString([], {
                      hour12: false,
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </span>
                  <span
                    className={`${
                      log.level === "error"
                        ? "text-red-400 font-bold"
                        : log.level === "success"
                        ? "text-green-400 font-bold"
                        : log.level === "system"
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
