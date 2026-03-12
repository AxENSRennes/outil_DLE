import { Outlet } from "react-router-dom";

import { appConfig } from "@/shared/config/app-config";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(206,110,56,0.16),_transparent_28%),linear-gradient(180deg,_#f6f0e7_0%,_#efe4d3_100%)] text-stone-900">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-8 sm:px-8 lg:px-10">
        <header className="flex items-center justify-between border-b border-stone-900/10 pb-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-stone-500">
              regulated workflow foundation
            </p>
            <h1 className="font-['Space_Grotesk',sans-serif] text-2xl font-semibold tracking-tight">
              {appConfig.title}
            </h1>
          </div>
          <div className="rounded-full border border-stone-900/10 bg-white/60 px-3 py-1 text-sm text-stone-600 shadow-sm backdrop-blur">
            Split-stack baseline
          </div>
        </header>
        <main className="flex-1 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
