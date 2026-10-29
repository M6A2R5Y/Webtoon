"use client";

import React, { useEffect, useState, useCallback } from "react";
import Navbar from "@/components/Navbar";
import PromptStudio from "@/components/PromptStudio";
import VideoPreview from "@/components/VideoPreview";
import HistoryGallery from "@/components/HistoryGallery";
import {
  AspectRatio,
  CostEstimate,
  DurationSeconds,
  GenerationMode,
  StylePreset,
  StudioStatus,
  VideoJob,
  deleteHistoryJob,
  fetchCostEstimate,
  fetchHistory,
  fetchStudioStatus,
  pollVideoJob,
  submitVideoGeneration,
} from "@/lib/api";
import { AlertTriangle, Sparkles } from "lucide-react";

export default function StudioHomePage() {
  // Studio Form State
  const [mode, setMode] = useState<GenerationMode>("text_to_video");
  const [prompt, setPrompt] = useState<string>(
    "A cyberpunk street food vendor cooking glowing ramen in neon rain at night"
  );
  const [stylePreset, setStylePreset] = useState<StylePreset>("cinematic");
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>("9:16");
  const [duration, setDuration] = useState<DurationSeconds>(5);
  const [sourceImageUrl, setSourceImageUrl] = useState<string | null>(null);

  // Backend Status, Cost Estimate, Active Job & History
  const [studioStatus, setStudioStatus] = useState<StudioStatus | null>(null);
  const [costEstimate, setCostEstimate] = useState<CostEstimate | null>(null);
  const [activeJob, setActiveJob] = useState<VideoJob | null>(null);
  const [history, setHistory] = useState<VideoJob[]>([]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Load initial studio status & history
  const refreshStudioAndHistory = useCallback(async () => {
    try {
      const [statusData, historyData] = await Promise.all([
        fetchStudioStatus(),
        fetchHistory(),
      ]);
      setStudioStatus(statusData);
      setHistory(historyData.items);
      setApiError(null);
      if (!activeJob && historyData.items.length > 0) {
        setActiveJob(historyData.items[0]);
      }
    } catch (err: any) {
      setApiError(
        "Cannot reach the FastAPI backend at http://localhost:8000. Make sure the Python server is running."
      );
    }
  }, [activeJob]);

  useEffect(() => {
    refreshStudioAndHistory();
  }, [refreshStudioAndHistory]);

  // Recalculate cost estimate whenever duration, aspect ratio, mode, or style changes
  useEffect(() => {
    let ignore = false;
    async function updateCost() {
      try {
        const est = await fetchCostEstimate({
          generation_type: mode,
          duration_seconds: duration,
          aspect_ratio: aspectRatio,
          style_preset: stylePreset,
        });
        if (!ignore) setCostEstimate(est);
      } catch {
        // Ignore if backend is offline during initial boot
      }
    }
    updateCost();
    return () => {
      ignore = true;
    };
  }, [mode, duration, aspectRatio, stylePreset]);

  // Automatic Polling Loop: Whenever `activeJob` is "queued" or "processing", poll every 2.5 seconds
  useEffect(() => {
    if (
      !activeJob ||
      (activeJob.status !== "queued" && activeJob.status !== "processing")
    ) {
      return;
    }

    const timer = setInterval(async () => {
      try {
        const updated = await pollVideoJob(activeJob.id);
        setActiveJob(updated);
        setHistory((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item))
        );
        if (updated.status === "completed" || updated.status === "failed") {
          const statusData = await fetchStudioStatus();
          setStudioStatus(statusData);
        }
      } catch {
        // Keep polling on transient hiccups
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [activeJob]);

  async function handleGenerateVideo(confirmPaid: boolean) {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const newJob = await submitVideoGeneration({
        generation_type: mode,
        prompt,
        style_preset: stylePreset,
        aspect_ratio: aspectRatio,
        duration_seconds: duration,
        source_image_url: mode === "image_to_video" ? sourceImageUrl : null,
        confirm_paid_generation: confirmPaid,
      });
      setActiveJob(newJob);
      setHistory((prev) => [newJob, ...prev]);
      const statusData = await fetchStudioStatus();
      setStudioStatus(statusData);
    } catch (err: any) {
      setApiError(err.message || "Failed to start video generation.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleReuseSettings(job: VideoJob) {
    setMode(job.generation_type);
    setPrompt(job.prompt);
    setStylePreset(job.style_preset);
    setAspectRatio(job.aspect_ratio);
    setDuration(job.duration_seconds);
    if (job.source_image_url) {
      setSourceImageUrl(job.source_image_url);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function handleDeleteJob(jobId: string) {
    try {
      await deleteHistoryJob(jobId);
      setHistory((prev) => prev.filter((j) => j.id !== jobId));
      if (activeJob?.id === jobId) {
        setActiveJob(null);
      }
    } catch (err: any) {
      setApiError(err.message || "Could not delete job.");
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#090A0F]">
      <Navbar studioStatus={studioStatus} />

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:py-8">
        {/* Top Banner if Backend is Unreachable or API Error Occurs */}
        {apiError && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
            <AlertTriangle className="h-5 w-5 shrink-0 text-red-400" />
            <span>{apiError}</span>
          </div>
        )}

        {/* Main Two-Column Studio Layout */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left Column: Prompt & Settings Studio (7 cols on desktop) */}
          <div className="lg:col-span-7">
            <PromptStudio
              mode={mode}
              setMode={setMode}
              prompt={prompt}
              setPrompt={setPrompt}
              stylePreset={stylePreset}
              setStylePreset={setStylePreset}
              aspectRatio={aspectRatio}
              setAspectRatio={setAspectRatio}
              duration={duration}
              setDuration={setDuration}
              sourceImageUrl={sourceImageUrl}
              setSourceImageUrl={setSourceImageUrl}
              costEstimate={costEstimate}
              studioStatus={studioStatus}
              isSubmitting={isSubmitting}
              onGenerate={handleGenerateVideo}
            />
          </div>

          {/* Right Column: Live Progress & Video Preview Player (5 cols on desktop) */}
          <div className="lg:col-span-5">
            <VideoPreview activeJob={activeJob} />
          </div>
        </div>

        {/* Bottom Section: User's Generation History Gallery */}
        <HistoryGallery
          history={history}
          activeJobId={activeJob?.id}
          onSelectJob={(job) => setActiveJob(job)}
          onReuseSettings={handleReuseSettings}
          onDeleteJob={handleDeleteJob}
        />
      </main>

      <footer className="mt-12 border-t border-studio-border bg-[#090A0F] py-5 text-center text-xs text-slate-500">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 sm:px-6">
          <span>
            VibeMotion AI Video Studio • Built with Next.js, FastAPI & SQLAlchemy
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            Modular Provider Architecture (fal.ai + Honest Demo Mode)
          </span>
        </div>
      </footer>
    </div>
  );
}
