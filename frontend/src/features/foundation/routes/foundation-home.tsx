import { ArrowRight, DatabaseZap, FileText, HeartPulse } from "lucide-react";

import { Button } from "@/shared/ui/button";

const readinessItems = [
  {
    title: "Backend API shell",
    description: "Django + DRF boots under /api/v1 with health and schema endpoints."
  },
  {
    title: "Frontend workspace",
    description: "Vite, React Router, TanStack Query, and the shared UI baseline are wired."
  },
  {
    title: "Runtime baseline",
    description: "Docker Compose and environment templates define a single local stack convention."
  }
];

export function FoundationHomePage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.35fr_0.95fr]">
      <section className="panel overflow-hidden p-8 sm:p-10">
        <div className="max-w-2xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-700/15 bg-emerald-50 px-3 py-1 text-sm text-emerald-800">
            <HeartPulse className="h-4 w-4" />
            Platform foundation ready
          </div>
          <h2 className="font-['Space_Grotesk',sans-serif] text-4xl font-semibold tracking-tight text-stone-950 sm:text-5xl">
            Split-stack workspace for regulated batch-record delivery.
          </h2>
          <p className="mt-5 max-w-xl text-base leading-7 text-stone-700">
            The repo now has a stable backend, frontend, database, and contract baseline so later
            stories can add workflow behavior without moving the foundations again.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild>
              <a href="/api/v1/schema/docs/">
                Open API docs
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
            <Button asChild variant="secondary">
              <a href="https://ui.shadcn.com/docs/installation/vite" rel="noreferrer" target="_blank">
                UI baseline
              </a>
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4">
        {readinessItems.map((item) => (
          <article className="panel p-6" key={item.title}>
            <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-900 text-stone-50">
              {item.title.includes("Backend") ? (
                <HeartPulse className="h-5 w-5" />
              ) : item.title.includes("Frontend") ? (
                <FileText className="h-5 w-5" />
              ) : (
                <DatabaseZap className="h-5 w-5" />
              )}
            </div>
            <h3 className="text-lg font-semibold text-stone-950">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-stone-700">{item.description}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
