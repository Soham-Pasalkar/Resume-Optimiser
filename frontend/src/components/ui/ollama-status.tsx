"use client";

import React, { useEffect, useState } from "react";
import { Cpu, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { getOllamaStatus, OllamaStatus } from "@/lib/api";

export const OllamaStatusWidget: React.FC = () => {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  const checkStatus = async () => {
    setLoading(true);
    const data = await getOllamaStatus();
    setStatus(data);
    setLoading(false);
  };

  useEffect(() => {
    checkStatus();
    // Poll every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="btn-soft flex items-center gap-2 px-3 py-1.5 text-xs select-none"
        title="Local AI Engine Status"
        aria-label="Local AI Engine Status"
      >
        <Cpu className="w-3.5 h-3.5 text-soft-blue" />
        {loading ? (
          <span className="flex items-center gap-1 text-soft-muted">
            <RefreshCw className="w-3 h-3 animate-spin" />
            Checking Ollama...
          </span>
        ) : status?.is_available ? (
          <span className="flex items-center gap-1.5 font-semibold text-soft-green-text">
            <span className="w-2 h-2 rounded-full bg-soft-green animate-pulse" />
            Ollama: {status.active_model}
          </span>
        ) : (
          <span className="flex items-center gap-1.5 font-semibold text-soft-orange-text">
            <span className="w-2 h-2 rounded-full bg-soft-orange" />
            Ollama Offline
          </span>
        )}
      </button>

      {/* Popover Details Card */}
      {showDetails && (
        <div className="absolute right-0 mt-2 w-72 surface p-4 z-50 text-left text-xs space-y-2.5">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
            <div className="flex items-center gap-1.5 font-bold text-soft-text">
              <Cpu className="w-4 h-4 text-soft-blue" />
              Local AI Engine (100% Free)
            </div>
            <button
              onClick={checkStatus}
              disabled={loading}
              className="p-1 hover:bg-slate-200/50 rounded"
              title="Refresh status"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-soft-muted ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between">
              <span className="text-soft-muted">Provider:</span>
              <span className="font-semibold text-soft-text">Ollama (Local)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-soft-muted">Daemon URL:</span>
              <span className="font-mono text-[11px] text-soft-text">
                {status?.base_url || "http://localhost:11434"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-soft-muted">Active Model:</span>
              <span className="font-semibold text-soft-blue">
                {status?.active_model || "llama3.1:8b"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-soft-muted">Operational Cost:</span>
              <span className="font-bold text-soft-green-text">$0.00 (Zero API Fee)</span>
            </div>
          </div>

          {status?.is_available ? (
            <div className="well p-2 text-soft-green-text flex items-start gap-1.5 text-[11px]">
              <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <span>Ollama daemon is active. Resumes and inferences run locally on your hardware.</span>
            </div>
          ) : (
            <div className="well p-2 text-soft-orange-text flex items-start gap-1.5 text-[11px]">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold">Ollama not detected.</p>
                <p className="text-[10px] text-soft-muted mt-0.5">
                  Run <code className="bg-slate-200 px-1 py-0.5 rounded">ollama serve</code> in your terminal.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
