"use client";

import React, { useState } from "react";
import {
  Wand2,
  Image as ImageIcon,
  Type,
  Upload,
  Sparkles,
  Loader2,
  AlertCircle,
  Check,
  Info,
  X,
} from "lucide-react";
import {
  AspectRatio,
  CostEstimate,
  DurationSeconds,
  GenerationMode,
  StylePreset,
  StudioStatus,
  enhancePrompt,
  uploadReferenceImage,
} from "@/lib/api";

interface PromptStudioProps {
  mode: GenerationMode;
  setMode: (mode: GenerationMode) => void;
  prompt: string;
  setPrompt: (prompt: string) => void;
  stylePreset: StylePreset;
  setStylePreset: (style: StylePreset) => void;
  aspectRatio: AspectRatio;
  setAspectRatio: (ratio: AspectRatio) => void;
  duration: DurationSeconds;
  setDuration: (duration: DurationSeconds) => void;
  sourceImageUrl: string | null;
  setSourceImageUrl: (url: string | null) => void;
  costEstimate: CostEstimate | null;
  studioStatus: StudioStatus | null;
  isSubmitting: boolean;
  onGenerate: (confirmPaid: boolean) => void;
}

const STYLE_OPTIONS: { id: StylePreset; label: string; desc: string }[] = [
  { id: "cinematic", label: "Cinematic Film", desc: "Anamorphic 35mm, dramatic lighting" },
  { id: "anime", label: "Modern Anime", desc: "Vibrant Shinkai sky, sakuga motion" },
  { id: "cyberpunk", label: "Cyberpunk Neon", desc: "Rainy neon streets, sci-fi glow" },
  { id: "3d_animation", label: "3D Animation", desc: "Pixar-style tactile 3D lighting" },
  { id: "photorealistic", label: "Photorealistic", desc: "Natural 8K documentary realism" },
  { id: "vintage_film", label: "1970s Vintage", desc: "16mm Kodak grain & warm halation" },
  { id: "dark_fantasy", label: "Dark Fantasy", desc: "Gothic mist, torchlight & embers" },
  { id: "commercial", label: "Product Ad", desc: "Crisp studio slow-motion macro" },
];

const ASPECT_RATIOS: { id: AspectRatio; label: string; sub: string; iconClass: string }[] = [
  { id: "9:16", label: "9:16 Vertical", sub: "TikTok / Reels / Shorts", iconClass: "w-3.5 h-6" },
  { id: "16:9", label: "16:9 Landscape", sub: "YouTube / Cinema", iconClass: "w-6 h-3.5" },
  { id: "1:1", label: "1:1 Square", sub: "Instagram / Feed", iconClass: "w-4 h-4" },
];

const QUICK_STARTER_PROMPTS = [
  "A cyberpunk street food vendor cooking glowing ramen in neon rain at night",
  "A golden retriever puppy running through a sunlit meadow of wildflowers in slow motion",
  "An astronaut discovering a bioluminescent crystal cave on an alien planet",
  "Luxury perfume bottle surrounded by splashing water droplets and golden light rays",
];

export default function PromptStudio({
  mode,
  setMode,
  prompt,
  setPrompt,
  stylePreset,
  setStylePreset,
  aspectRatio,
  setAspectRatio,
  duration,
  setDuration,
  sourceImageUrl,
  setSourceImageUrl,
  costEstimate,
  studioStatus,
  isSubmitting,
  onGenerate,
}: PromptStudioProps) {
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [enhanceBadge, setEnhanceBadge] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedMeta, setUploadedMeta] = useState<{
    filename: string;
    width: number;
    height: number;
    size_kb: number;
  } | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [confirmPaid, setConfirmPaid] = useState(false);

  const isLivePaidMode = Boolean(studioStatus && !studioStatus.is_demo_mode);

  async function handleEnhancePrompt() {
    if (!prompt.trim() || prompt.trim().length < 3) {
      setLocalError("Type at least a few words (e.g., 'a dragon flying over mountains') before enhancing.");
      return;
    }
    setLocalError(null);
    setIsEnhancing(true);
    setEnhanceBadge(null);
    try {
      const res = await enhancePrompt({
        prompt: prompt.trim(),
        style_preset: stylePreset,
        aspect_ratio: aspectRatio,
      });
      setPrompt(res.enhanced_prompt);
      setEnhanceBadge(
        res.enhancer_source === "gemini"
          ? "Enhanced with Gemini AI"
          : "Enhanced with Cinematic Director Engine"
      );
    } catch (err: any) {
      setLocalError(err.message || "Could not enhance prompt.");
    } finally {
      setIsEnhancing(false);
    }
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLocalError(null);
    setIsUploading(true);
    try {
      const result = await uploadReferenceImage(file);
      setSourceImageUrl(result.image_url);
      setUploadedMeta({
        filename: file.name,
        width: result.width,
        height: result.height,
        size_kb: result.size_kb,
      });
    } catch (err: any) {
      setLocalError(err.message || "Image upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (prompt.trim().length < 3) {
      setLocalError("Please enter a scene description (at least 3 characters).");
      return;
    }
    if (mode === "image_to_video" && !sourceImageUrl) {
      setLocalError("Please upload a reference image for Image-to-Video mode.");
      return;
    }
    if (isLivePaidMode && !confirmPaid) {
      setLocalError("Please check the cost confirmation box before submitting a paid API request.");
      return;
    }
    onGenerate(confirmPaid || !isLivePaidMode);
  }

  return (
    <form
      onSubmit={handleFormSubmit}
      className="flex flex-col gap-5 rounded-2xl border border-studio-border bg-studio-card p-5 shadow-xl sm:p-6"
    >
      {/* Mode Switcher Tabs: Text-to-Video vs Image-to-Video */}
      <div className="grid grid-cols-2 gap-2 rounded-xl bg-[#090A0F] p-1.5 border border-studio-border">
        <button
          type="button"
          onClick={() => setMode("text_to_video")}
          className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all ${
            mode === "text_to_video"
              ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md shadow-purple-600/20"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Type className="h-4 w-4" />
          <span>Text-to-Video</span>
        </button>
        <button
          type="button"
          onClick={() => setMode("image_to_video")}
          className={`flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-medium transition-all ${
            mode === "image_to_video"
              ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md shadow-purple-600/20"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <ImageIcon className="h-4 w-4" />
          <span>Image-to-Video</span>
        </button>
      </div>

      {/* Image Upload Dropzone (Visible in Image-to-Video Mode) */}
      {mode === "image_to_video" && (
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
            1. Reference Image to Animate
          </label>
          {!sourceImageUrl ? (
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-purple-500/40 bg-[#090A0F]/70 px-4 py-6 text-center transition hover:border-purple-400 hover:bg-purple-500/5">
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileChange}
                className="hidden"
                disabled={isUploading}
              />
              {isUploading ? (
                <div className="flex items-center gap-2 text-sm text-purple-300">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Validating & uploading image...</span>
                </div>
              ) : (
                <>
                  <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-purple-500/15 text-purple-400">
                    <Upload className="h-5 w-5" />
                  </div>
                  <p className="text-sm font-medium text-slate-200">
                    Click to upload an image (JPG, PNG, WEBP)
                  </p>
                  <p className="mt-1 text-xs text-slate-400">
                    Max {studioStatus?.max_upload_size_mb || 10} MB • Validated server-side
                  </p>
                </>
              )}
            </label>
          ) : (
            <div className="flex items-center justify-between rounded-xl border border-purple-500/30 bg-[#090A0F] p-3">
              <div className="flex items-center gap-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={sourceImageUrl}
                  alt="Uploaded reference"
                  className="h-14 w-14 rounded-lg object-cover border border-studio-border"
                />
                <div>
                  <p className="text-sm font-medium text-white">
                    {uploadedMeta?.filename || "Reference Image Ready"}
                  </p>
                  {uploadedMeta && (
                    <p className="text-xs text-slate-400">
                      {uploadedMeta.width}×{uploadedMeta.height}px • {uploadedMeta.size_kb} KB
                    </p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSourceImageUrl(null);
                  setUploadedMeta(null);
                }}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-red-400"
                title="Remove image"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Scene Prompt Input + AI Prompt Enhancer */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label
            htmlFor="scene-prompt"
            className="text-xs font-semibold uppercase tracking-wider text-slate-300"
          >
            {mode === "image_to_video"
              ? "2. Describe Motion & Camera Action"
              : "1. Scene Description Prompt"}
          </label>
          <button
            type="button"
            onClick={handleEnhancePrompt}
            disabled={isEnhancing || !prompt.trim()}
            className="flex items-center gap-1.5 rounded-lg border border-purple-500/40 bg-purple-500/15 px-3 py-1 text-xs font-semibold text-purple-200 transition hover:bg-purple-500/25 disabled:opacity-50"
          >
            {isEnhancing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Wand2 className="h-3.5 w-3.5 text-purple-300" />
            )}
            <span>AI Enhance Prompt</span>
          </button>
        </div>

        <textarea
          id="scene-prompt"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder={
            mode === "image_to_video"
              ? "Describe how the image should move (e.g., 'Camera slowly pushes in while neon lights flicker and rain falls')..."
              : "Describe your video idea (e.g., 'A cinematic drone shot over a misty waterfall at sunrise')..."
          }
          className="w-full rounded-xl border border-studio-border bg-[#090A0F] p-3.5 text-sm text-white placeholder-slate-500 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
        />

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
          <span>{prompt.length} / 1500 characters</span>
          {enhanceBadge && (
            <span className="flex items-center gap-1 text-purple-300">
              <Sparkles className="h-3 w-3" />
              {enhanceBadge}
            </span>
          )}
        </div>

        {/* Starter Inspiration Pills */}
        <div className="pt-1">
          <p className="mb-1.5 text-[11px] font-medium text-slate-400">
            Try a sample idea:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_STARTER_PROMPTS.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setPrompt(sample);
                  setEnhanceBadge(null);
                }}
                className="rounded-lg border border-studio-border bg-[#090A0F] px-2.5 py-1 text-left text-[11px] text-slate-300 transition hover:border-purple-500/40 hover:text-white"
              >
                {sample.slice(0, 48)}...
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Aspect Ratio & Duration Selectors */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Aspect Ratio */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
            Aspect Ratio
          </label>
          <div className="grid grid-cols-3 gap-2">
            {ASPECT_RATIOS.map((item) => {
              const active = aspectRatio === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setAspectRatio(item.id)}
                  className={`flex flex-col items-center justify-center rounded-xl border p-2.5 text-center transition ${
                    active
                      ? "border-purple-500 bg-purple-500/15 text-white"
                      : "border-studio-border bg-[#090A0F] text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <div
                    className={`mb-1.5 rounded-sm border-2 ${
                      active ? "border-purple-400 bg-purple-400/20" : "border-slate-500"
                    } ${item.iconClass}`}
                  />
                  <span className="text-xs font-semibold">{item.id}</span>
                  <span className="text-[10px] text-slate-400 leading-tight mt-0.5">
                    {item.sub.split(" / ")[0]}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Duration Selector */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
            Clip Duration
          </label>
          <div className="grid grid-cols-2 gap-2 h-[74px]">
            {([5, 10] as DurationSeconds[]).map((sec) => {
              const active = duration === sec;
              return (
                <button
                  key={sec}
                  type="button"
                  onClick={() => setDuration(sec)}
                  className={`flex flex-col items-center justify-center rounded-xl border p-2.5 transition ${
                    active
                      ? "border-blue-500 bg-blue-500/15 text-white"
                      : "border-studio-border bg-[#090A0F] text-slate-400 hover:border-slate-700 hover:text-slate-200"
                  }`}
                >
                  <span className="text-base font-bold">{sec}s</span>
                  <span className="text-[11px] text-slate-400">
                    {sec === 5 ? "Standard Short" : "Extended Story"}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Visual Style Preset Grid */}
      <div className="space-y-2">
        <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
          Visual Style Preset
        </label>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {STYLE_OPTIONS.map((style) => {
            const active = stylePreset === style.id;
            return (
              <button
                key={style.id}
                type="button"
                onClick={() => setStylePreset(style.id)}
                className={`flex flex-col items-start rounded-xl border p-2.5 text-left transition ${
                  active
                    ? "border-purple-500 bg-purple-500/15 text-white shadow-sm"
                    : "border-studio-border bg-[#090A0F] text-slate-300 hover:border-slate-700"
                }`}
              >
                <div className="flex w-full items-center justify-between">
                  <span className="text-xs font-semibold">{style.label}</span>
                  {active && <Check className="h-3.5 w-3.5 text-purple-400" />}
                </div>
                <span className="mt-1 text-[10px] text-slate-400 line-clamp-1">
                  {style.desc}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Cost Estimator & Paid Consent Box */}
      {costEstimate && (
        <div className="rounded-xl border border-studio-border bg-[#090A0F] p-3.5 text-xs">
          <div className="flex items-start gap-2.5">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-400" />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">
                  Estimated Generation Cost:
                </span>
                <span
                  className={`rounded-md px-2 py-0.5 font-bold ${
                    costEstimate.is_demo
                      ? "bg-emerald-500/15 text-emerald-300"
                      : "bg-blue-500/20 text-blue-300"
                  }`}
                >
                  ${costEstimate.estimated_cost_usd.toFixed(2)} USD
                </span>
              </div>
              <p className="text-slate-400">{costEstimate.cost_explanation}</p>
            </div>
          </div>

          {isLivePaidMode && (
            <label className="mt-3 flex cursor-pointer items-center gap-2 border-t border-studio-border pt-2.5 text-slate-200">
              <input
                type="checkbox"
                checked={confirmPaid}
                onChange={(e) => setConfirmPaid(e.target.checked)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-900 text-purple-600 focus:ring-purple-500"
              />
              <span>
                I confirm spending ~${costEstimate.estimated_cost_usd.toFixed(2)} USD on my
                connected {studioStatus?.active_provider.toUpperCase()} API account.
              </span>
            </label>
          )}
        </div>
      )}

      {/* Validation / Error Banner */}
      {localError && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
          <span>{localError}</span>
        </div>
      )}

      {/* Primary Generate Video Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 py-3.5 text-sm font-bold text-white shadow-lg shadow-purple-600/25 transition hover:from-purple-500 hover:to-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Submitting Generation Job...</span>
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            <span>
              Generate {duration}s {aspectRatio} Video{" "}
              {costEstimate?.is_demo
                ? "(Demo Mode • Free)"
                : costEstimate
                ? `(~$${costEstimate.estimated_cost_usd.toFixed(2)})`
                : ""}
            </span>
          </>
        )}
      </button>
    </form>
  );
}
