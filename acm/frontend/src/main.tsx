import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { ToastProvider } from "./components/toast/ToastProvider";
import { PrototypeProvider } from "./state/PrototypeContext";
import { fixtureRepo } from "./data/repository";
import "./styles/globals.css";

const queryClient = new QueryClient();

void fixtureRepo.hydrateProjects().catch(() => {
  // The access page exposes connection state; fixture reads remain available offline.
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PrototypeProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </PrototypeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
