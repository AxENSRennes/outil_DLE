import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/routes/app-layout";
import { FoundationHomePage } from "@/features/foundation/routes/foundation-home";
import { BatchExecutionPage } from "@/features/execution/pages/BatchExecutionPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <FoundationHomePage />
      },
      {
        path: "batches/:batchId/execution",
        element: <BatchExecutionPage />
      }
    ]
  }
]);
