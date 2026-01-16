export interface LogMessage {
  type: "log";
  level: "info" | "error" | "success" | "system";
  message: string;
  timestamp: number;
}

export interface ChatMessage {
  role: "tutor" | "student";
  content: string;
}

export interface LevelEstimate {
  level: number;
  confidence: number;
}

export interface StudentInfo {
  name: string;
  topic: string;
}

export interface StateUpdate {
  type: "state_update";
  history: ChatMessage[];
  estimates: LevelEstimate[];
  current_level: number;
  current_confidence: number;
}

export type AgentStatus = "idle" | "running" | "stopping";
