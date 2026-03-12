import type { PropsWithChildren } from "react";

import { QueryClientProvider } from "@tanstack/react-query";

import { appQueryClient } from "@/app/providers/query-client";

export function AppProviders({ children }: PropsWithChildren) {
  return <QueryClientProvider client={appQueryClient}>{children}</QueryClientProvider>;
}
