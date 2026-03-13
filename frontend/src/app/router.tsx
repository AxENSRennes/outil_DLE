import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/routes/app-layout";
import { FoundationHomePage } from "@/features/foundation/routes/foundation-home";
import { PreQaReviewPage } from "@/features/pre-qa-review/routes/PreQaReviewPage";

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
        path: "review/:batchId",
        element: <PreQaReviewPage />
      }
    ]
  }
]);
