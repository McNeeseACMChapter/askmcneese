import { motion } from "framer-motion";
import { slideInLeft } from "../../lib/motion";
import type { AskStatus, PipelineInfo } from "../../hooks/useAsk";

interface TypingIndicatorProps {
  status?: AskStatus;
  pipeline?: PipelineInfo;
}

export function TypingIndicator({ status = "searching", pipeline }: TypingIndicatorProps) {
  const message = pipeline?.message || getDefaultMessage(status);
  const sourcesFound = pipeline?.sourcesFound;
  
  return (
    <motion.div
      variants={slideInLeft}
      initial="hidden"
      animate="visible"
      exit="exit"
      className="flex justify-start"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-mcneese-blue">
          <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
        </div>
        <div className="rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3 shadow-soft min-w-[200px]">
          <span className="sr-only">AskMcNeese is {message.toLowerCase()}</span>
          
          {/* Pipeline Steps */}
          <div className="space-y-2">
            {/* Current Status */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-mcneese-blue/60"
                    animate={{
                      scale: [0.6, 1, 0.6],
                      opacity: [0.4, 1, 0.4],
                    }}
                    transition={{
                      duration: 1.2,
                      repeat: Infinity,
                      delay: i * 0.15,
                      ease: "easeInOut",
                    }}
                  />
                ))}
              </div>
              <motion.span
                className="text-sm font-medium text-text-primary"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                {message}
              </motion.span>
            </div>
            
            {/* Pipeline Progress */}
            {pipeline && pipeline.steps.length > 0 && (
              <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
                {pipeline.steps.map((step, idx) => (
                  <motion.div
                    key={`${step.step}-${idx}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-center gap-2 text-xs"
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${
                      step.status === "completed" ? "bg-green-500" : 
                      step.status === "failed" ? "bg-red-500" : "bg-yellow-500"
                    }`} />
                    <span className="text-text-muted capitalize">{step.step}</span>
                    {step.duration_ms && (
                      <span className="text-text-muted/60">{step.duration_ms}ms</span>
                    )}
                    {step.status === "completed" && (
                      <span className="text-green-600">✓</span>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
            
            {/* Sources Found */}
            {sourcesFound !== undefined && sourcesFound > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs text-text-muted"
              >
                📚 {sourcesFound} source{sourcesFound !== 1 ? "s" : ""} found
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function getDefaultMessage(status: AskStatus): string {
  switch (status) {
    case "connecting": return "Connecting to server...";
    case "searching": return "Searching mcneese.edu...";
    case "generating": return "Generating answer from sources...";
    case "complete": return "Done";
    case "error": return "An error occurred";
    default: return "Processing...";
  }
}
