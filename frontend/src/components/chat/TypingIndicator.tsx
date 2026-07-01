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
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-mcneese-blue to-mcneese-dark">
          <motion.svg 
            className="h-3.5 w-3.5 text-white" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor" 
            strokeWidth={2}
            animate={{ rotate: status === "searching" || status === "generating" ? 360 : 0 }}
            transition={{ duration: 2, repeat: status === "searching" || status === "generating" ? Infinity : 0, ease: "linear" }}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </motion.svg>
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
    case "searching": return "Searching knowledge base...";
    case "generating": return "Generating answer...";
    case "complete": return "Done";
    case "error": return "An error occurred";
    default: return "Processing...";
  }
}
