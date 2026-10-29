"use client";

import React from "react";
import { Film, Sparkles, ShieldAlert, CheckCircle2, Coins, Zap } from "lucide-react";
import { StudioStatus } from "@/lib/api";

interface NavbarProps {
  studioStatus: StudioStatus | null;
}

export default function Navbar({ studioStatus }: NavbarProps) {
  const isDemo = studioStatus ? studioStatus.is_demo_mode : true;

  return (
    <header className="sticky top-0 z-30 border-b border-studio-border bg-[#090A0F]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-6">
        {/* Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 shadow-lg shadow-purple-600/25">
            <Film className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-gradient-to-r from-white via-purple-200 to-blue-300 bg-clip-text text-lg font-bold tracking-tight text-transparent">
                VibeMotion AI
              </span>
              <span className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-purple-300">
                Studio
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Short-Form AI Video Generator for Reels, TikTok & Shorts
            </p>
          </div>
        </div>

        {/* Status & Cost / Quota Indicators */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Provider Badge (Demo vs Live API) */}
          {isDemo ? (
            <div
              title="No FAL_KEY configured in backend/.env. Using honest Demo Mode with labeled sample clips at $0.00 cost."
              className="flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300"
            >
              <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
              <span>Demo Mode (Sample Clips • $0.00)</span>
            </div>
          ) : (
            <div
              title={`Connected to ${studioStatus?.provider_display_name}`}
              className="flex items-center gap-1.5 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              <span>Live API ({studioStatus?.active_provider.toUpperCase()})</span>
            </div>
          )}

          {/* Daily Quota Pill */}
          {studioStatus && (
            <div className="flex items-center gap-3 rounded-xl border border-studio-border bg-studio-card px-3 py-1.5 text-xs text-slate-300">
              <div className="flex items-center gap-1.5" title="Daily Generation Quota">
                <Zap className="h-3.5 w-3.5 text-purple-400" />
                <span>
                  Quota:{" "}
                  <strong className="text-white">
                    {studioStatus.generations_used_today}/{studioStatus.daily_limit}
                  </strong>
                </span>
              </div>
              <span className="text-slate-600">|</span>
              <div className="flex items-center gap-1.5" title="Estimated API Spend Today">
                <Coins className="h-3.5 w-3.5 text-blue-400" />
                <span>
                  Today:{" "}
                  <strong className="text-white">
                    ${studioStatus.total_estimated_spend_today_usd.toFixed(2)}
                  </strong>
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
