"use client";

import React from "react";
import {
  Clock,
  Play,
  Trash2,
  Download,
  RotateCcw,
  CheckCircle2,
  Loader2,
  XCircle,
  ShieldAlert,
} from "lucide-react";
import { VideoJob, getDownloadUrl } from "@/lib/api";

interface HistoryGalleryProps {
  history: VideoJob[];
  activeJobId?: string;
  onSelectJob: (job: VideoJob) => void;
  onReuseSettings: (job: VideoJob) => void;
  onDeleteJob: (jobId: string) => void;
}

export default function HistoryGallery({
  history,
  activeJobId,
  onSelectJob,
  onReuseSettings,
  onDeleteJob,
}: HistoryGalleryProps) {
  return (
    <section className="mt-8 rounded-2xl border border-studio-border bg-studio-card p-5 shadow-xl sm:p-6">
      <div className="mb-4 flex items-center justify-between border-b border-studio-border pb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-purple-400" />
          <h2 className="text-base font-bold text-white">
            Your Generation History ({history.length})
          </h2>
        </div>
        <span className="text-xs text-slate-400">
          Saved in SQLite • Click any card to preview or reuse settings
        </span>
      </div>

      {history.length === 0 ? (
        <div className="rounded-xl border border-dashed border-studio-border bg-[#090A0F]/60 py-10 text-center">
          <p className="text-sm text-slate-400">
            No videos generated yet. Your completed and queued clips will appear here automatically.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {history.map((job) => {
            const isSelected = job.id === activeJobId;
            return (
              <div
                key={job.id}
                onClick={() => onSelectJob(job)}
                className={`group flex cursor-pointer flex-col justify-between rounded-xl border p-4 transition ${
                  isSelected
                    ? "border-purple-500 bg-purple-500/10"
                    : "border-studio-border bg-[#090A0F] hover:border-slate-700"
                }`}
              >
                <div>
                  {/* Top row: status + demo/live tag + timestamp */}
                  <div className="mb-2.5 flex items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 text-xs font-semibold">
                      {job.status === "completed" && (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Completed
                        </span>
                      )}
                      {(job.status === "queued" || job.status === "processing") && (
                        <span className="flex items-center gap-1 text-blue-400">
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          {job.status} ({job.progress_percent}%)
                        </span>
                      )}
                      {job.status === "failed" && (
                        <span className="flex items-center gap-1 text-red-400">
                          <XCircle className="h-3.5 w-3.5" />
                          Failed
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5">
                      {job.is_demo ? (
                        <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/30">
                          DEMO
                        </span>
                      ) : (
                        <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                          LIVE
                        </span>
                      )}
                      <span className="text-[11px] text-slate-500">
                        {new Date(job.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  </div>

                  {/* Prompt snippet */}
                  <p className="text-xs font-medium text-slate-200 line-clamp-2 mb-3">
                    {job.prompt}
                  </p>

                  {/* Settings pills */}
                  <div className="flex flex-wrap gap-1.5 text-[10px] text-slate-400 mb-3">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-slate-300 capitalize">
                      {job.style_preset.replace("_", " ")}
                    </span>
                    <span className="rounded bg-slate-800 px-2 py-0.5">
                      {job.aspect_ratio}
                    </span>
                    <span className="rounded bg-slate-800 px-2 py-0.5">
                      {job.duration_seconds}s
                    </span>
                    <span className="rounded bg-slate-800 px-2 py-0.5">
                      {job.generation_type === "image_to_video" ? "I2V" : "T2V"}
                    </span>
                  </div>
                </div>

                {/* Card Footer Actions */}
                <div
                  className="flex items-center justify-between border-t border-studio-border pt-2.5"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => onSelectJob(job)}
                      className="flex items-center gap-1 rounded-lg bg-purple-500/15 px-2.5 py-1 text-[11px] font-semibold text-purple-300 hover:bg-purple-500/25"
                    >
                      <Play className="h-3 w-3" />
                      Preview
                    </button>
                    <button
                      type="button"
                      onClick={() => onReuseSettings(job)}
                      title="Load prompt and settings into Studio"
                      className="flex items-center gap-1 rounded-lg border border-studio-border px-2 py-1 text-[11px] text-slate-300 hover:border-slate-600 hover:text-white"
                    >
                      <RotateCcw className="h-3 w-3" />
                      Reuse
                    </button>
                  </div>

                  <div className="flex items-center gap-1">
                    {job.status === "completed" && job.video_url && (
                      <a
                        href={getDownloadUrl(job.id)}
                        download
                        title="Download MP4"
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-blue-400"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </a>
                    )}
                    <button
                      type="button"
                      onClick={() => onDeleteJob(job.id)}
                      title="Delete from history"
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-red-400"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
