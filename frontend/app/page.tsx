"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

import {
  Play,
  Square,
  User,
  Bot,
  Activity,
  BarChart2,
  Terminal,
  MessageCircle,
  Zap,
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
    name: "Student",
    topic: "Ready to Learn",
  });

  // Mobile Tab State
  const [activeTab, setActiveTab] = useState<"chat" | "stats">("chat");
  const [finalScores, setFinalScores] = useState<{
    mse: string | null;
    tutoring: string | null;
  }>({ mse: null, tutoring: null });

  // Refs for auto-scrolling
  const logContainerRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [chatHistory]);

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5000/api/stream");
    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "log") {
        setLogs((prev) => [...prev.slice(-99), data]);
        if (data.message.includes("Processing")) {
          const match = data.message.match(/Processing (.*?) - (.*)/);
          if (match) {
            setStudentInfo({ name: match[1], topic: match[2] });
            setChatHistory([]);
            setEstimates([]);
            setCurrentLevel(0);
            setCurrentConfidence(0);
            setFinalScores({ mse: null, tutoring: null });
          }
        }
        if (data.message.includes("FINAL_MSE_SCORE:"))
          setFinalScores((p) => ({
            ...p,
            mse: data.message.split(":")[1].trim(),
          }));
        if (data.message.includes("FINAL_TUTORING_SCORE:"))
          setFinalScores((p) => ({
            ...p,
            tutoring: data.message.split(":")[1].trim(),
          }));
      } else if (data.type === "state_update") {
        setChatHistory(data.history);
        setEstimates(data.estimates);
        setCurrentLevel(data.current_level);
        setCurrentConfidence(data.current_confidence);
      }
    };
    return () => eventSource.close();
  }, []);

  const toggleAgent = async () => {
    if (status === "idle") {
      setStatus("running");
      setLogs([]);
      setFinalScores({ mse: null, tutoring: null });
      setActiveTab("chat");
      try {
        await fetch("http://localhost:5000/api/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ set_type: "mini_dev" }),
        });
      } catch (e) {
        console.error(e);
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
    <div className="flex flex-col h-[100dvh] bg-slate-50 font-sans text-slate-800 overflow-hidden">
      {/* 1. Navbar */}
      <nav className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-sm z-20">
        <div className="flex items-center gap-1">
          <span className="font-black text-2xl tracking-tighter text-knowunity-green">
            Knowunity
          </span>
          <span className="bg-slate-100 text-slate-500 text-[10px] px-1.5 py-0.5 rounded ml-2 font-bold uppercase tracking-wider">
            Agent
          </span>
        </div>

        <button
          onClick={toggleAgent}
          className={`flex items-center gap-2 px-5 py-2 rounded-full font-bold text-sm transition-all shadow-md active:scale-95 ${
            status === "running"
              ? "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100"
              : "bg-knowunity-green text-white hover:bg-emerald-600"
          }`}
        >
          {status === "running" ? (
            <Square size={14} fill="currentColor" />
          ) : (
            <Play size={14} fill="currentColor" />
          )}
          <span>{status === "running" ? "End Session" : "Start Class"}</span>
        </button>
      </nav>

      {/* 2. Main Area */}
      <main className="flex-1 overflow-hidden relative flex flex-col lg:grid lg:grid-cols-12 lg:gap-6 lg:p-6 bg-slate-50">
        {/* --- CHAT SECTION --- */}
        <section
          className={`
          ${activeTab === "chat" ? "flex" : "hidden"} 
          lg:flex col-span-7 flex-col h-full bg-white lg:rounded-2xl lg:shadow-sm lg:border border-slate-200 overflow-hidden
        `}
        >
          {/* Header */}
          <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-white shrink-0 z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center font-bold shadow-sm">
                {studentInfo.name[0]}
              </div>
              <div>
                <h2 className="font-bold text-slate-800 leading-tight">
                  {studentInfo.name}
                </h2>
                <p className="text-xs text-slate-500 font-medium">
                  {studentInfo.topic}
                </p>
              </div>
            </div>

            {/* Live Stats HUD */}
            <div className="flex items-center gap-4 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-100">
              <div className="flex flex-col items-end">
                <span className="text-[9px] uppercase font-bold text-slate-400">
                  Level
                </span>
                <span className="text-sm font-black text-slate-700">
                  {currentLevel > 0 ? currentLevel.toFixed(1) : "-"}
                </span>
              </div>
              <div className="w-px h-6 bg-slate-200"></div>
              <div className="flex flex-col items-end">
                <span className="text-[9px] uppercase font-bold text-slate-400">
                  Conf
                </span>
                <span
                  className={`text-sm font-black ${
                    currentConfidence > 0.8
                      ? "text-emerald-500"
                      : "text-amber-500"
                  }`}
                >
                  {(currentConfidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          {/* Messages Container */}
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50/30 custom-scrollbar scroll-smooth"
          >
            {chatHistory.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center opacity-40 gap-3">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
                  <Zap size={32} className="text-slate-400" />
                </div>
                <p className="text-slate-500 font-medium">
                  Waiting for student connection...
                </p>
              </div>
            )}

            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 max-w-[95%] lg:max-w-[85%] ${
                  msg.role === "tutor" ? "ml-auto flex-row-reverse" : ""
                } animate-in fade-in slide-in-from-bottom-2 duration-300 relative group`}
              >
                {/* Avatar */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm border ${
                    msg.role === "tutor"
                      ? "bg-knowunity-green text-white border-emerald-500"
                      : "bg-white border-slate-200 text-slate-400"
                  }`}
                >
                  {msg.role === "tutor" ? (
                    <Bot size={16} />
                  ) : (
                    <User size={16} />
                  )}
                </div>

                {/* Bubble */}
                <div className="flex flex-col">
                  {/* Turn Indicator (NEW) */}
                  <span
                    className={`text-[10px] font-bold text-slate-400 mb-1 uppercase tracking-wide ${
                      msg.role === "tutor" ? "text-right" : "text-left"
                    }`}
                  >
                    Turn {Math.floor(i / 2) + 1}
                  </span>

                  <div
                    className={`px-4 py-3 text-[15px] rounded-2xl shadow-sm leading-relaxed ${
                      msg.role === "tutor"
                        ? "bg-knowunity-green text-white rounded-tr-none"
                        : "bg-white border border-slate-200 text-slate-700 rounded-tl-none"
                    }`}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                      components={{
                        p: ({ node, ...props }) => (
                          <p className="mb-0 leading-relaxed" {...props} />
                        ),
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} className="h-1" />
          </div>
        </section>

        {/* --- STATS SECTION --- */}
        <section
          className={`
           ${activeTab === "stats" ? "flex" : "hidden"} 
           lg:flex col-span-5 flex-col gap-4 h-full p-4 lg:p-0 overflow-hidden
        `}
        >
          {/* Card: Student Level */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 shrink-0">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-slate-700 flex items-center gap-2 text-sm uppercase tracking-wide">
                <BarChart2 size={16} className="text-blue-500" /> Assessment
              </h3>
              <span className="text-3xl font-black text-slate-800">
                {currentLevel > 0 ? currentLevel.toFixed(1) : "-"}
              </span>
            </div>
            <div className="h-3 w-full flex gap-1">
              {[1, 2, 3, 4, 5].map((lvl) => (
                <div
                  key={lvl}
                  className={`flex-1 rounded-full transition-all duration-500 ${
                    currentLevel >= lvl
                      ? "bg-blue-500"
                      : currentLevel > lvl - 1
                      ? "bg-blue-200"
                      : "bg-slate-100"
                  }`}
                />
              ))}
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-bold uppercase">
              <span>Struggling</span>
              <span>Mastery</span>
            </div>
          </div>

          {/* Card: Confidence */}
          <div className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 shrink-0">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-bold text-slate-700 flex items-center gap-2 text-sm uppercase tracking-wide">
                <Activity size={16} className="text-emerald-500" /> Certainty
              </h3>
              <span className="text-xl font-bold text-slate-600">
                {(currentConfidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-700 rounded-full ${
                  currentConfidence > 0.8 ? "bg-emerald-500" : "bg-amber-400"
                }`}
                style={{ width: `${currentConfidence * 100}%` }}
              />
            </div>
          </div>

          {/* Log / Notebook */}
          <div className="flex-1 bg-slate-900 rounded-2xl shadow-lg border border-slate-800 flex flex-col overflow-hidden min-h-[200px]">
            <div className="px-4 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-widest">
                <Terminal size={12} /> System Logs
              </div>
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-red-500/20"></div>
                <div className="w-2 h-2 rounded-full bg-yellow-500/20"></div>
                <div className="w-2 h-2 rounded-full bg-green-500/20"></div>
              </div>
            </div>
            <div
              ref={logContainerRef}
              className="flex-1 overflow-y-auto p-4 space-y-1.5 font-mono text-[11px] custom-scrollbar"
            >
              {logs.map((log, i) => (
                <div
                  key={i}
                  className="flex gap-3 hover:bg-white/5 p-1 rounded transition-colors"
                >
                  <span className="text-slate-600 shrink-0 select-none">
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
                        ? "text-emerald-400 font-bold"
                        : log.level === "system"
                        ? "text-blue-400"
                        : "text-slate-300"
                    }`}
                  >
                    {log.message}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Final Results */}
          {(finalScores.mse || finalScores.tutoring) && (
            <div className="bg-gradient-to-r from-violet-600 to-indigo-600 text-white p-5 rounded-xl shadow-lg animate-in slide-in-from-bottom-4 shrink-0">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-[10px] text-indigo-200 uppercase font-bold tracking-widest mb-1">
                    MSE Accuracy
                  </p>
                  <p className="text-3xl font-black tracking-tight">
                    {Number(finalScores.mse).toFixed(4)}
                  </p>
                </div>
                <div className="w-px h-10 bg-white/20"></div>
                <div className="text-right">
                  <p className="text-[10px] text-indigo-200 uppercase font-bold tracking-widest mb-1">
                    Tutoring Score
                  </p>
                  <p className="text-3xl font-black text-emerald-300 tracking-tight">
                    {finalScores.tutoring}/5
                  </p>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* 3. Mobile Bottom Tab Bar */}
      <div className="lg:hidden shrink-0 h-16 bg-white border-t border-slate-200 flex justify-around items-center px-2 z-30 pb-safe">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex flex-col items-center gap-1 p-2 px-6 rounded-xl transition-all ${
            activeTab === "chat"
              ? "text-knowunity-green bg-emerald-50"
              : "text-slate-400"
          }`}
        >
          <MessageCircle size={20} />
          <span className="text-[10px] font-bold">Chat</span>
        </button>

        <button
          onClick={() => setActiveTab("stats")}
          className={`flex flex-col items-center gap-1 p-2 px-6 rounded-xl transition-all ${
            activeTab === "stats"
              ? "text-knowunity-green bg-emerald-50"
              : "text-slate-400"
          }`}
        >
          <BarChart2 size={20} />
          <span className="text-[10px] font-bold">Progress</span>
        </button>
      </div>
    </div>
  );
}
