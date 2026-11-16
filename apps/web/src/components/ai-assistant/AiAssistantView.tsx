"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Send,
  RefreshCw,
  ShieldAlert,
  Cpu,
  Layers,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  Activity,
  ArrowRightLeft,
  FileText,
  Search,
  ExternalLink,
  ChevronRight,
  User,
  Bot,
  Zap,
  Trash2,
} from "lucide-react";
import { backendApiClient } from "@/services/api/backendApiClient";
import {
  AIChatResponse,
  ChatMessage,
  EvidenceItem,
  ProviderStatus,
  PipelineComparisonResponse,
  OperationalSummaryResponse,
  EvidenceGapAnalysis,
} from "@/services/api/advancedAiTypes";

const QUICK_QUESTIONS = [
  "Which pipeline currently has the highest inspection priority and why?",
  "Why is PIPE-SEC-4B-92 classified as critical?",
  "Are there contradictions in the evidence for this segment?",
  "Which rovers are available and eligible to inspect this pipeline?",
  "Can the system dispatch a rover to inspect this leak immediately?",
  "What caused the model to predict a 7-day failure risk of 78%?",
  "What are the tradeoffs between inspecting pipeline A vs pipeline B today?",
  "What hydraulic impact would a rupture on this segment have?",
  "What evidence supports the leak hypothesis versus sensor anomaly?",
  "What are we missing to make a confident repair decision?",
  "Summarize the operational situation across the network today.",
  "What should an operator investigate next?",
];

export function AiAssistantView() {
  const [activeTab, setActiveTab] = useState<"chat" | "compare" | "summary" | "gaps">("chat");
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [providerStatus, setProviderStatus] = useState<ProviderStatus | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);

  // Advanced Analytics State
  const [compareSegmentA, setCompareSegmentA] = useState("PIPE-SEC-4B-92");
  const [compareSegmentB, setCompareSegmentB] = useState("PIPE-HRB-02-19");
  const [comparisonResult, setComparisonResult] = useState<PipelineComparisonResponse | null>(null);
  const [operationalSummary, setOperationalSummary] = useState<OperationalSummaryResponse | null>(null);
  const [evidenceGaps, setEvidenceGaps] = useState<EvidenceGapAnalysis | null>(null);
  const [gapSegmentId, setGapSegmentId] = useState("PIPE-SEC-4B-92");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProviderStatus();
    loadInitialChat();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadProviderStatus = async () => {
    try {
      const status = await backendApiClient.getProviderStatus();
      setProviderStatus(status);
    } catch (e) {
      console.error("Failed to load provider status", e);
    }
  };

  const loadInitialChat = async () => {
    try {
      const convs = await backendApiClient.listAiConversations(1);
      if (convs.length > 0) {
        const detail = await backendApiClient.getAiConversationDetail(convs[0].id);
        setConversationId(detail.id);
        setMessages(detail.messages);
      }
    } catch (e) {
      console.error("Failed to load initial conversation", e);
    }
  };

  const handleClearConversation = async () => {
    if (!conversationId) return;
    try {
      await backendApiClient.deleteAiConversation(conversationId);
    } catch (e) {
      console.error("Failed to delete conversation", e);
    }
    setConversationId(null);
    setMessages([]);
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || query).trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: `USER-${Date.now()}`,
      role: "user",
      content: text,
      model_used: "client-input",
      provider_used: "OPERATOR",
      validation_status: "VALIDATED",
      timestamp: new Date().toISOString(),
      evidence_references: [],
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setIsLoading(true);

    try {
      const res: AIChatResponse = await backendApiClient.chatWithAiAssistant({
        conversation_id: conversationId || undefined,
        query: text,
        user_id: "OPERATOR-SUPERVISOR-01",
      });

      setConversationId(res.conversation_id);

      const assistantMessage: ChatMessage = {
        id: res.message_id,
        role: "assistant",
        content: res.content,
        intent: res.intent,
        model_used: res.model_used,
        provider_used: res.provider_used,
        validation_status: res.validation_status,
        timestamp: res.timestamp,
        evidence_references: res.supporting_evidence.map((e) => e.evidence_id),
        supporting_evidence: res.supporting_evidence,
        claims: res.claims,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `ERR-${Date.now()}`,
        role: "assistant",
        content: `Error communicating with operational intelligence backend: ${err.message || "Unknown error"}`,
        model_used: "fallback",
        provider_used: "ERROR",
        validation_status: "ERROR",
        timestamp: new Date().toISOString(),
        evidence_references: [],
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunComparison = async () => {
    setIsLoading(true);
    try {
      const res = await backendApiClient.comparePipelines([compareSegmentA, compareSegmentB]);
      setComparisonResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadSummary = async () => {
    setIsLoading(true);
    try {
      const res = await backendApiClient.getOperationalSummary();
      setOperationalSummary(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadEvidenceGaps = async () => {
    setIsLoading(true);
    try {
      const res = await backendApiClient.analyzeEvidenceGaps(gapSegmentId);
      setEvidenceGaps(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getClassificationBadge = (cls: string) => {
    switch (cls) {
      case "MEASURED":
        return "bg-emerald-950/80 text-emerald-300 border-emerald-800/80";
      case "SIMULATED":
        return "bg-cyan-950/80 text-cyan-300 border-cyan-800/80";
      case "DERIVED":
        return "bg-purple-950/80 text-purple-300 border-purple-800/80";
      case "PREDICTED":
        return "bg-amber-950/80 text-amber-300 border-amber-800/80";
      case "OPERATOR_ENTERED":
        return "bg-blue-950/80 text-blue-300 border-blue-800/80";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-5.5rem)] w-full overflow-hidden bg-slate-950 text-slate-100 rounded-lg border border-slate-800">
      {/* 1. Header & Provider Telemetry Bar */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 bg-slate-900/90 px-4 py-2.5 gap-2 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold tracking-tight text-white">
                Operational AI Decision Assistant
              </h2>
              <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
                TASK 13
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Evidence-grounded decision intelligence with strict ontological segregation & non-fabricated explainability
            </p>
          </div>
        </div>

        {/* Telemetry Pills */}
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          {/* User Identity & Role Badge (Task 13.6) */}
          <div className="flex items-center gap-1.5 rounded-md border border-cyan-800/80 bg-cyan-950/40 px-2.5 py-1 text-cyan-300">
            <User className="h-3 w-3 text-cyan-400" />
            <span className="text-slate-400">User:</span>
            <span className="font-semibold text-cyan-200">
              {backendApiClient.getCurrentUser()?.username || "operator"}
            </span>
            <span className="rounded bg-cyan-900/60 px-1.5 py-0.2 text-[9px] font-mono font-bold text-cyan-300 border border-cyan-700/60">
              {backendApiClient.getCurrentUser()?.role || "OPERATOR"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/80 px-2.5 py-1">
            <Cpu className="h-3 w-3 text-cyan-400" />
            <span className="text-slate-400">Provider:</span>
            <span className="font-mono font-semibold text-cyan-300">
              {providerStatus?.active_provider || "DETERMINISTIC"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/80 px-2.5 py-1">
            <Layers className="h-3 w-3 text-purple-400" />
            <span className="text-slate-400">Model:</span>
            <span className="font-mono text-purple-300">
              {providerStatus?.active_model || "deterministic-grounded-engine"}
            </span>
          </div>

          {providerStatus?.is_live_verified ? (
            <div
              className="flex items-center gap-1.5 rounded-md border border-emerald-900/60 bg-emerald-950/40 px-2.5 py-1 text-emerald-300"
              title={providerStatus?.live_verification_status || "Live API connected and verified"}
            >
              <CheckCircle2 className="h-3 w-3 text-emerald-400" />
              <span className="font-semibold">LIVE-VERIFIED</span>
            </div>
          ) : (
            <div
              className="flex items-center gap-1.5 rounded-md border border-amber-900/60 bg-amber-950/40 px-2.5 py-1 text-amber-300"
              title={providerStatus?.live_verification_status || "No live API key configured. Deterministic fallback active."}
            >
              <AlertTriangle className="h-3 w-3 text-amber-400" />
              <span className="font-semibold">NOT LIVE-VERIFIED</span>
            </div>
          )}

          <div className="flex items-center gap-1.5 rounded-md border border-rose-900/60 bg-rose-950/40 px-2.5 py-1 text-rose-300">
            <ShieldAlert className="h-3 w-3 text-rose-400" />
            <span>Actuators Disabled</span>
          </div>

          {conversationId && (
            <button
              onClick={handleClearConversation}
              disabled={isLoading}
              title="Reset conversation state"
              className="flex items-center gap-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-rose-950/40 hover:border-rose-800/60 px-2.5 py-1 text-slate-300 hover:text-rose-300 transition-colors"
            >
              <Trash2 className="h-3 w-3 text-slate-400 hover:text-rose-400" />
              <span>Reset Chat</span>
            </button>
          )}

          <div className="hidden lg:flex items-center gap-1.5 rounded-md border border-amber-900/60 bg-amber-950/40 px-2.5 py-1 text-amber-300">
            <span>[SIMULATED ENGINE]</span>
          </div>
        </div>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-900/50 px-4 text-xs font-medium shrink-0">
        <button
          onClick={() => setActiveTab("chat")}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 transition-colors ${
            activeTab === "chat"
              ? "border-cyan-500 text-cyan-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Bot className="h-3.5 w-3.5" />
          Decision Assistant
        </button>
        <button
          onClick={() => {
            setActiveTab("compare");
            if (!comparisonResult) handleRunComparison();
          }}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 transition-colors ${
            activeTab === "compare"
              ? "border-cyan-500 text-cyan-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ArrowRightLeft className="h-3.5 w-3.5" />
          Pipeline Tradeoff Comparison
        </button>
        <button
          onClick={() => {
            setActiveTab("summary");
            if (!operationalSummary) handleLoadSummary();
          }}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 transition-colors ${
            activeTab === "summary"
              ? "border-cyan-500 text-cyan-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          Network Operational Summary
        </button>
        <button
          onClick={() => {
            setActiveTab("gaps");
            if (!evidenceGaps) handleLoadEvidenceGaps();
          }}
          className={`flex items-center gap-1.5 border-b-2 px-3 py-2 transition-colors ${
            activeTab === "gaps"
              ? "border-cyan-500 text-cyan-400 font-semibold"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Search className="h-3.5 w-3.5" />
          Evidence Gap Analysis
        </button>
      </div>

      {/* 3. Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === "chat" && (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Quick Question Pills */}
            <div className="border-b border-slate-800/80 bg-slate-900/30 px-4 py-2 shrink-0 overflow-x-auto no-scrollbar">
              <div className="flex items-center gap-2 whitespace-nowrap">
                <span className="text-[11px] font-semibold text-slate-400 flex items-center gap-1">
                  <Zap className="h-3 w-3 text-amber-400" /> Suggested:
                </span>
                {QUICK_QUESTIONS.slice(0, 6).map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q)}
                    disabled={isLoading}
                    className="rounded-full border border-slate-700/70 bg-slate-800/50 hover:bg-slate-700/70 px-2.5 py-1 text-[11px] text-slate-300 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Message Thread */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
                  <div className="h-12 w-12 rounded-full bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <h3 className="text-base font-semibold text-white">
                    AQUA CREW Evidence-Grounded Assistant
                  </h3>
                  <p className="text-xs text-slate-400 max-w-md">
                    Ask questions regarding inspection priorities, acoustic leak anomalies, digital twin hydraulic impacts,
                    rover fleet feasibility, or multi-factor infrastructure vulnerabilities.
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-xl text-left pt-2">
                    {QUICK_QUESTIONS.slice(0, 4).map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSendMessage(q)}
                        className="rounded-lg border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 p-2.5 text-xs text-slate-300 transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-4xl ${msg.role === "user" ? "ml-auto" : "mr-auto"}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                      msg.role === "user"
                        ? "bg-slate-800 border-slate-700 text-slate-300"
                        : "bg-cyan-950/80 border-cyan-800/60 text-cyan-400"
                    }`}
                  >
                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-200">
                        {msg.role === "user" ? "Operator" : "AQUA Decision Assistant"}
                      </span>
                      {msg.model_used && (
                        <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                          {msg.model_used}
                        </span>
                      )}
                      {msg.validation_status === "VALIDATED" && (
                        <span className="flex items-center gap-0.5 rounded bg-emerald-950/80 px-1.5 py-0.5 text-[10px] text-emerald-400 border border-emerald-800/60">
                          <CheckCircle2 className="h-2.5 w-2.5" /> GROUNDED
                        </span>
                      )}
                      {msg.validation_status === "FLAGGED" && (
                        <span className="flex items-center gap-0.5 rounded bg-rose-950/80 px-1.5 py-0.5 text-[10px] text-rose-400 border border-rose-800/60">
                          <ShieldAlert className="h-2.5 w-2.5" /> REJECTED
                        </span>
                      )}
                      <span className="text-[10px] text-slate-500">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* Message Bubble */}
                    <div
                      className={`rounded-lg border p-3.5 text-xs leading-relaxed shadow-sm ${
                        msg.role === "user"
                          ? "bg-cyan-950/30 border-cyan-800/40 text-slate-200"
                          : "bg-slate-900/80 border-slate-800 text-slate-200"
                      }`}
                    >
                      <div className="prose prose-invert prose-xs max-w-none whitespace-pre-wrap font-sans">
                        {msg.content}
                      </div>

                      {/* Cited Evidence Badges */}
                      {msg.supporting_evidence && msg.supporting_evidence.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                          <div className="text-[10px] font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
                            <Layers className="h-3 w-3 text-cyan-400" /> Grounded Evidence Citations:
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.supporting_evidence.map((ev) => (
                              <button
                                key={ev.evidence_id}
                                onClick={() => setSelectedEvidence(ev)}
                                className={`rounded px-2 py-0.5 text-[10px] font-mono border transition-colors flex items-center gap-1 hover:brightness-125 ${getClassificationBadge(
                                  ev.classification
                                )}`}
                              >
                                <span>[{ev.classification}]</span>
                                <span>{ev.metric_name}: {ev.metric_value}</span>
                                {ev.is_stale && (
                                  <span className="rounded bg-rose-950 px-1 text-[9px] text-rose-300 border border-rose-800 ml-1">
                                    STALE
                                  </span>
                                )}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3 max-w-4xl mr-auto items-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 animate-pulse">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-2.5 text-xs text-slate-400">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                    <span>Retrieving multi-source evidence & synthesizing answer...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input Bar */}
            <div className="border-t border-slate-800 bg-slate-900/90 p-3 shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask the operational assistant (e.g. 'Why is PIPE-SEC-4B-92 critical?')..."
                  disabled={isLoading}
                  className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                <button
                  type="submit"
                  disabled={!query.trim() || isLoading}
                  className="flex items-center gap-1.5 rounded-md bg-cyan-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-cyan-500 disabled:opacity-50 transition-colors"
                >
                  <Send className="h-3.5 w-3.5" />
                  <span>Ask</span>
                </button>
              </form>
            </div>
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === "compare" && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 gap-2">
              <div>
                <h3 className="text-sm font-bold text-white">Pipeline Tradeoff Comparative Analysis</h3>
                <p className="text-xs text-slate-400">
                  Side-by-side evaluation of structural vulnerability, hydraulic consequence, and inspection urgency.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={compareSegmentA}
                  onChange={(e) => setCompareSegmentA(e.target.value)}
                  className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-white"
                />
                <span className="text-xs text-slate-400">vs</span>
                <input
                  type="text"
                  value={compareSegmentB}
                  onChange={(e) => setCompareSegmentB(e.target.value)}
                  className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-white"
                />
                <button
                  onClick={handleRunComparison}
                  disabled={isLoading}
                  className="rounded bg-cyan-600 hover:bg-cyan-500 px-3 py-1 text-xs font-semibold text-white transition-colors"
                >
                  Compare
                </button>
              </div>
            </div>

            {comparisonResult && (
              <div className="space-y-4">
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-300">
                  <div className="font-semibold text-cyan-400 mb-1">Comparative Strategic Synthesis:</div>
                  <p>{comparisonResult.comparative_summary}</p>
                </div>

                <div className="overflow-x-auto rounded-lg border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900 border-b border-slate-800 text-[11px] font-semibold text-slate-400">
                      <tr>
                        <th className="p-2.5">Pipeline Conduit</th>
                        <th className="p-2.5">Priority Tier</th>
                        <th className="p-2.5">Vulnerability</th>
                        <th className="p-2.5">Health Condition</th>
                        <th className="p-2.5">Consequence Dimension</th>
                        <th className="p-2.5">Recommended Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {comparisonResult.segments.map((s) => (
                        <tr
                          key={s.segment_id}
                          className={s.segment_id === comparisonResult.highest_priority_segment_id ? "bg-cyan-950/20" : ""}
                        >
                          <td className="p-2.5 font-medium text-white">
                            <div>{s.name}</div>
                            <div className="font-mono text-[10px] text-slate-400">{s.segment_id}</div>
                          </td>
                          <td className="p-2.5">
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                                s.priority_tier === "CRITICAL"
                                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                                  : "bg-amber-950 text-amber-300 border border-amber-800"
                              }`}
                            >
                              {s.priority_tier} ({s.inspection_priority.toFixed(1)})
                            </span>
                          </td>
                          <td className="p-2.5 font-mono">{s.vulnerability_score.toFixed(1)} / 100</td>
                          <td className="p-2.5 font-mono">{s.health_score.toFixed(1)} ({s.health_category})</td>
                          <td className="p-2.5">{s.diameter_mm}mm ({s.material})</td>
                          <td className="p-2.5 text-slate-300">{s.recommended_action}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Summary Tab */}
        {activeTab === "summary" && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">Metropolitan Network Operational Summary</h3>
                <p className="text-xs text-slate-400">
                  Aggregated health condition, active acoustic alerts, and recommended operator interventions.
                </p>
              </div>
              <button
                onClick={handleLoadSummary}
                disabled={isLoading}
                className="flex items-center gap-1 rounded bg-slate-800 hover:bg-slate-700 px-3 py-1 text-xs text-slate-200 transition-colors"
              >
                <RefreshCw className="h-3 w-3" /> Refresh
              </button>
            </div>

            {operationalSummary && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                    <div className="text-[10px] text-slate-400">Network Urgency</div>
                    <div className="text-lg font-bold text-rose-400">{operationalSummary.network_urgency}</div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                    <div className="text-[10px] text-slate-400">Critical Conduits</div>
                    <div className="text-lg font-bold text-amber-400">{operationalSummary.critical_assets_count}</div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                    <div className="text-[10px] text-slate-400">Active Inferences</div>
                    <div className="text-lg font-bold text-cyan-400">{operationalSummary.new_incidents_count}</div>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
                    <div className="text-[10px] text-slate-400">Pending Actions</div>
                    <div className="text-lg font-bold text-purple-400">{operationalSummary.pending_recommendations_count}</div>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-200">
                  <div className="font-semibold text-cyan-400 mb-1">Executive Situation Narrative:</div>
                  <p className="leading-relaxed">{operationalSummary.narrative_summary}</p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs">
                  <div className="font-semibold text-amber-400 mb-2">Unresolved Network Risks:</div>
                  <ul className="list-disc pl-4 space-y-1 text-slate-300">
                    {operationalSummary.unresolved_risks.map((r, idx) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs">
                  <div className="font-semibold text-emerald-400 mb-2">Recommended Next Actions:</div>
                  <ul className="list-disc pl-4 space-y-1 text-slate-300">
                    {operationalSummary.recommended_next_actions.map((a, idx) => (
                      <li key={idx}>{a}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Evidence Gaps Tab */}
        {activeTab === "gaps" && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 gap-2">
              <div>
                <h3 className="text-sm font-bold text-white">Sensor Uncertainty & Evidence Gap Analysis</h3>
                <p className="text-xs text-slate-400">
                  Evaluates missing sensory evidence to achieve decision confidence before physical excavation.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={gapSegmentId}
                  onChange={(e) => setGapSegmentId(e.target.value)}
                  className="rounded border border-slate-700 bg-slate-900 px-2.5 py-1 text-xs text-white"
                />
                <button
                  onClick={handleLoadEvidenceGaps}
                  disabled={isLoading}
                  className="rounded bg-cyan-600 hover:bg-cyan-500 px-3 py-1 text-xs font-semibold text-white transition-colors"
                >
                  Analyze
                </button>
              </div>
            </div>

            {evidenceGaps && (
              <div className="space-y-4">
                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 flex items-center justify-between">
                  <div>
                    <div className="text-xs font-bold text-white">{evidenceGaps.segment_name}</div>
                    <div className="font-mono text-[10px] text-slate-400">{evidenceGaps.segment_id}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-slate-400">Data Completeness</div>
                    <div className="text-lg font-bold text-cyan-400">
                      {evidenceGaps.overall_data_completeness_pct.toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs">
                  <div className="font-semibold text-amber-400 mb-2">Missing Evidence Indicators:</div>
                  <ul className="list-disc pl-4 space-y-1.5 text-slate-300">
                    {evidenceGaps.missing_indicators.map((m, idx) => (
                      <li key={idx}>{m}</li>
                    ))}
                  </ul>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs text-slate-300">
                  <div className="font-semibold text-purple-400 mb-1">Uncertainty Impact on Authorization:</div>
                  <p>{evidenceGaps.uncertainty_impact_description}</p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 text-xs">
                  <div className="font-semibold text-emerald-400 mb-2">Recommended Sensory Interventions:</div>
                  <ul className="list-disc pl-4 space-y-1 text-slate-300">
                    {evidenceGaps.recommended_sensor_installations.map((inst, idx) => (
                      <li key={idx}>{inst}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Side Evidence Inspector Drawer */}
        {selectedEvidence && (
          <div className="w-80 border-l border-slate-800 bg-slate-900/95 p-4 flex flex-col shrink-0 overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                <Layers className="h-4 w-4 text-cyan-400" /> Evidence Detail
              </div>
              <button
                onClick={() => setSelectedEvidence(null)}
                className="text-slate-400 hover:text-white text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[10px] text-slate-400">Evidence ID:</span>
                <div className="font-mono text-cyan-300 font-semibold">{selectedEvidence.evidence_id}</div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Classification:</span>
                <div>
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-[10px] font-mono border font-bold ${getClassificationBadge(
                      selectedEvidence.classification
                    )}`}
                  >
                    {selectedEvidence.classification}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Source Provenance:</span>
                <div className="font-mono text-slate-200">{selectedEvidence.source_module}</div>
                <div className="font-mono text-[10px] text-slate-500">
                  {selectedEvidence.source_table} [{selectedEvidence.source_record_id}]
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Observed Metric:</span>
                <div className="font-semibold text-white">
                  {selectedEvidence.metric_name}:{" "}
                  <span className="font-mono text-cyan-400">
                    {selectedEvidence.metric_value !== null ? selectedEvidence.metric_value : "N/A"} {selectedEvidence.metric_unit}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Summary:</span>
                <div className="text-slate-300 text-[11px] leading-relaxed bg-slate-950 p-2 rounded border border-slate-800">
                  {selectedEvidence.summary}
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Confidence Rating:</span>
                <div className="font-mono text-emerald-400 font-semibold">
                  {(selectedEvidence.confidence * 100).toFixed(0)}% ({selectedEvidence.validation_status})
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400">Calibration & Hardware Link:</span>
                <div className="flex flex-col gap-1 mt-0.5">
                  <div className="flex items-center gap-1 text-[11px]">
                    <span className="text-slate-400">Calibration:</span>
                    <span className="font-mono text-cyan-300 font-semibold">
                      {selectedEvidence.calibration_status || "UNVERIFIED_VIRTUAL"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px]">
                    <span className="text-slate-400">Hardware Link:</span>
                    <span
                      className={`font-mono font-semibold ${
                        selectedEvidence.hardware_connected ? "text-emerald-400" : "text-amber-400"
                      }`}
                    >
                      {selectedEvidence.hardware_connected ? "PHYSICAL (Connected)" : "VIRTUAL (Disconnected)"}
                    </span>
                  </div>
                  {selectedEvidence.is_stale && (
                    <div className="flex items-center gap-1 text-[11px] text-rose-400 bg-rose-950/40 border border-rose-900/60 p-1.5 rounded mt-1">
                      <AlertTriangle className="h-3 w-3 shrink-0" />
                      <span>
                        Stale Observation ({selectedEvidence.age_hours ? selectedEvidence.age_hours.toFixed(1) : ">24"}h old)
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 space-y-0.5">
                <div>Simulation: {selectedEvidence.is_simulated ? "true (virtual)" : "false"}</div>
                <div>Source Engine: {selectedEvidence.source}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

