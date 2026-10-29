"use client";

import React, { useState } from "react";
import {
  Download,
  Share2,
  Sparkles,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  Film,
  Check,
} from "lucide-react";
import { VideoJob, getDownloadUrl } from "@/lib/api";

interface VideoPreviewProps {
  activeJob: VideoJob | null;
}

export default function VideoPreview({ activeJob }: VideoPreviewProps) {
  const [copied, setCopied] = useState(false);

  if (!activeJob) {
    return (
      <div className="flex h-full min-h-[420px] flex-col items-center justify-center rounded-2xl border border-studio-border bg-studio-card p-8 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 border border-purple-500/30">
          <Film className="h-8 w-8 text-purple-400" />
        </div>
        <h3 className="text-lg font-bold text-white">Your Video Preview Studio</h3>
        <p className="mt-2 max-w-sm text-sm text-slate-400">
          Enter a prompt on the left, enhance it with AI camera & lighting directives, and click{" "}
          <strong className="text-purple-300">Generate Video</strong> to watch your clip come to life.
        </p>
      </div>
    );
  }

  const isQueuedOrProcessing =
    activeJob.status === "queued" || activeJob.status === "processing";

  // Frame aspect ratio styling for preview container
  const aspectContainerClass =
    activeJob.aspect_ratio === "9:16"
      ? "aspect-[9/16] max-w-[300px]"
      : activeJob.aspect_ratio === "1:1"
      ? "aspect-square max-w-[400px]"
      : "aspect-video w-full";

  async function handleCopyShareLink() {
    if (!activeJob?.video_url) return;
    try {
      await navigator.clipboard.writeText(activeJob.video_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
    }
  }

  return (
    <div className="flex flex-col justify-between rounded-2xl border border-studio-border bg-studio-card p-5 shadow-xl sm:p-6">
      {/* Header Bar with Status Badge & Honest Demo Label */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-studio-border pb-3.5">
        <div className="flex items-center gap-2">
          {activeJob.status === "queued" && (
            <span className="flex items-center gap-1.5 rounded-full bg-amber-500/15 border border-amber-500/40 px-3 py-1 text-xs font-semibold text-amber-300">
              <Clock className="h-3.5 w-3.5 animate-pulse" />
              Queued in GPU Pipeline ({activeJob.progress_percent}%)
            </span>
          )}
          {activeJob.status === "processing" && (
            <span className="flex items-center gap-1.5 rounded-full bg-blue-500/15 border border-blue-500/40 px-3 py-1 text-xs font-semibold text-blue-300">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Rendering Frames ({activeJob.progress_percent}%)
            </span>
          )}
          {activeJob.status === "completed" && (
            <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 border border-emerald-500/40 px-3 py-1 text-xs font-semibold text-emerald-300">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Completed ({activeJob.duration_seconds}s • {activeJob.aspect_ratio})
            </span>
          )}
          {activeJob.status === "failed" && (
            <span className="flex items-center gap-1.5 rounded-full bg-red-500/15 border border-red-500/40 px-3 py-1 text-xs font-semibold text-red-300">
              <XCircle className="h-3.5 w-3.5" />
              Generation Failed
            </span>
          )}
        </div>

        {activeJob.is_demo && (
          <span className="flex items-center gap-1 rounded-md bg-amber-500/15 border border-amber-500/40 px-2.5 py-1 text-[11px] font-semibold text-amber-300">
            <ShieldAlert className="h-3.5 w-3.5" />
            DEMO SAMPLE VIDEO (No API Key Configured)
          </span>
        )}
      </div>

      {/* Main Viewport: Progress Loader OR Error State OR Video Player */}
      <div className="my-2 flex flex-1 flex-col items-center justify-center rounded-xl bg-[#090A0F] p-4 border border-studio-border min-h-[340px]">
        {isQueuedOrProcessing && (
          <div className="flex w-full max-w-md flex-col items-center text-center space-y-4 py-8">
            <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-purple-500/10 border border-purple-500/30">
              <Loader2 className="h-8 w-8 animate-spin text-purple-400" />
            </div>
            <div className="space-y-1">
              <h4 className="text-base font-bold text-white">
                {activeJob.status === "queued"
                  ? "Job Queued — Allocating GPU Worker..."
                  : "Synthesizing Motion & Lighting..."}
              </h4>
              <p className="text-xs text-slate-400">
                {activeJob.is_demo
                  ? "Simulating asynchronous video pipeline in Demo Mode (~10 seconds)..."
                  : "Cloud AI video rendering typically takes 30 to 90 seconds. Polling automatically..."}
              </p>
            </div>

            {/* Progress Bar */}
            <div className="w-full overflow-hidden rounded-full bg-slate-800 h-2.5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                style={{ width: `${Math.max(8, activeJob.progress_percent)}%` }}
              />
            </div>
            <span className="text-xs font-mono text-purple-300">
              {activeJob.progress_percent}% Complete
            </span>
          </div>
        )}

        {activeJob.status === "failed" && (
          <div className="max-w-md text-center space-y-3 py-8">
            <XCircle className="mx-auto h-12 w-12 text-red-400" />
            <h4 className="text-base font-bold text-white">Video Generation Failed</h4>
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
              {activeJob.error_message || "An unexpected provider error occurred."}
            </p>
          </div>
        )}

        {activeJob.status === "completed" && activeJob.video_url && (
          <div className={`relative mx-auto overflow-hidden rounded-xl border border-studio-border bg-black shadow-2xl ${aspectContainerClass}`}>
            <video
              key={activeJob.video_url}
              src={activeJob.video_url}
              controls
              autoPlay
              loop
              playsInline
              className="h-full w-full object-cover"
            />
            {activeJob.is_demo && (
              <div className="pointer-events-none absolute top-2 left-2 rounded bg-black/75 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-amber-300 border border-amber-500/40">
                Demo Sample Clip
              </div>
            )}
          </div>
        )}
      </div>

      {/* Prompt Metadata & Action Buttons (Download / Share) */}
      <div className="mt-4 space-y-3 border-t border-studio-border pt-4">
        <div className="rounded-xl bg-[#090A0F] p-3 border border-studio-border">
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400 mb-1">
            <span className="rounded bg-purple-500/15 px-2 py-0.5 text-purple-300 font-medium capitalize">
              {activeJob.style_preset.replace("_", " ")}
            </span>
            <span>•</span>
            <span>{activeJob.generation_type === "image_to_video" ? "Image-to-Video" : "Text-to-Video"}</span>
            <span>•</span>
            <span>Aspect: {activeJob.aspect_ratio}</span>
            <span>•</span>
            <span>Duration: {activeJob.duration_seconds}s</span>
          </div>
          <p className="text-xs text-slate-200 line-clamp-2" title={activeJob.enhanced_prompt || activeJob.prompt}>
            <strong className="text-slate-400">Prompt: </strong>
            {activeJob.prompt}
          </p>
        </div>

        {activeJob.status === "completed" && activeJob.video_url && (
          <div className="flex flex-wrap gap-2.5">
            <a
              href={getDownloadUrl(activeJob.id)}
              download
              className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 px-4 py-2.5 text-xs font-bold text-white shadow-md transition hover:from-purple-500 hover:to-blue-500"
            >
              <Download className="h-4 w-4" />
              <span>Download MP4</span>
            </a>
            <button
              type="button"
              onClick={handleCopyShareLink}
              className="flex items-center justify-center gap-2 rounded-xl border border-studio-border bg-[#090A0F] px-4 py-2.5 text-xs font-semibold text-slate-200 transition hover:border-purple-500/50 hover:text-white"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 text-emerald-400" />
                  <span className="text-emerald-300">Link Copied!</span>
                </>
              ) : (
                <>
                  <Share2 className="h-4 w-4" />
                  <span>Copy Video Link</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
