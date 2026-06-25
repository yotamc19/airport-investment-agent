import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useVoiceInput } from "@/hooks/useVoiceInput";
import { useVoiceOutput } from "@/hooks/useVoiceOutput";

type ToolCall = {
  tool: string;
  input: Record<string, unknown>;
  result_preview: string;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
};

const SUGGESTIONS = [
  "Which airports in New England are strong candidates for terminal expansion?",
  "Compare LA and Santa Ana airport congestion levels.",
  "What is the percentage of long haul flights out of Anchorage airport?",
  "What is the unmet flight demand in SFO airport and why?",
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { isListening, transcript, startListening, stopListening, isSupported: sttSupported } = useVoiceInput();
  const { isSpeaking, speak, stop: stopSpeaking, isSupported: ttsSupported } = useVoiceOutput();
  const [autoSpeak, setAutoSpeak] = useState(false);
  const autoSpeakRef = useRef(autoSpeak);
  autoSpeakRef.current = autoSpeak;

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (transcript) setInput(transcript);
  }, [transcript]);

  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
    el.scrollTop = el.scrollHeight;
  }, [input]);

  async function sendMessage(text: string) {
    if (!text.trim() || isLoading) return;
    if (isListening) stopListening();

    const userMsg: Message = { role: "user", content: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    inputRef.current?.focus();

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text.trim(), history }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);

      const data = await res.json();
      setHistory(data.history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response, toolCalls: data.tool_calls },
      ]);
      if (autoSpeakRef.current && ttsSupported) speak(data.response);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Request failed"}` },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage(input);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  function formatToolInput(input: Record<string, unknown>): string {
    const parts = Object.entries(input).map(([k, v]) =>
      typeof v === "string" ? `${k}="${v}"` : `${k}=${JSON.stringify(v)}`
    );
    return parts.join(", ");
  }

  return (
    <div className="flex h-screen flex-col bg-bg">
      <header className="shrink-0 border-b border-border bg-surface px-6 py-4">
        <h1 className="text-lg font-semibold text-heading">
          Airport Investment Intelligence
        </h1>
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted">
            AI-powered analysis of US airport modernization opportunities
          </p>
          {ttsSupported && (
            <label className="flex items-center gap-2 text-xs text-muted cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoSpeak}
                onChange={(e) => setAutoSpeak(e.target.checked)}
                className="accent-primary"
              />
              Auto-speak
            </label>
          )}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.length === 0 && !isLoading && (
            <div className="py-12">
              <p className="mb-6 text-center text-muted">
                Ask about airport investment opportunities, congestion metrics, or regional comparisons.
              </p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="rounded-[var(--w-radius-card)] border border-border bg-surface px-4 py-3 text-left text-sm text-secondary transition-colors hover:border-primary hover:bg-primary-tint"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-[var(--w-radius-message)] px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-white"
                    : "bg-surface text-body shadow-sm ring-1 ring-border"
                }`}
              >
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="mb-3 space-y-1.5 border-b border-border pb-3">
                    <p className="text-xs font-medium text-muted">
                      Tools called:
                    </p>
                    {msg.toolCalls.map((tc, j) => (
                      <div
                        key={j}
                        className="rounded-md bg-primary-tint px-2.5 py-1.5 font-mono text-xs text-heading"
                      >
                        {tc.tool}({formatToolInput(tc.input)})
                      </div>
                    ))}
                  </div>
                )}
                {msg.role === "user" ? (
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                ) : (
                  <>
                    <div className="prose prose-sm max-w-none prose-headings:text-heading prose-p:text-body prose-strong:text-heading prose-a:text-accent [&_table]:w-full [&_table]:text-xs [&_th]:px-3 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold [&_th]:bg-surface-alt [&_td]:px-3 [&_td]:py-2 [&_table]:border-collapse [&_th]:border [&_th]:border-border [&_td]:border [&_td]:border-border [&_table]:overflow-x-auto">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                    {ttsSupported && (
                      <button
                        type="button"
                        onClick={() => isSpeaking ? stopSpeaking() : speak(msg.content)}
                        className="mt-2 flex items-center gap-1 text-xs text-muted hover:text-primary transition-colors"
                        aria-label={isSpeaking ? "Stop speaking" : "Read aloud"}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5">
                          {isSpeaking ? (
                            <rect x="5" y="5" width="10" height="10" rx="1.5" />
                          ) : (
                            <path d="M10 3.75a.75.75 0 00-1.264-.546L5.203 6H3.75A.75.75 0 003 6.75v6.5c0 .414.336.75.75.75h1.453l3.533 2.796A.75.75 0 0010 16.25V3.75zM15.95 5.05a.75.75 0 00-1.06 1.06 4.5 4.5 0 010 6.364.75.75 0 001.06 1.06 6 6 0 000-8.485z" />
                          )}
                        </svg>
                        <span>{isSpeaking ? "Stop" : "Listen"}</span>
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-[var(--w-radius-message)] bg-surface px-4 py-3 shadow-sm ring-1 ring-border">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-primary" />
                  <span className="ml-2 text-xs text-muted">Analyzing...</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0 border-t border-border bg-surface p-4">
        <form onSubmit={handleSubmit} className="mx-auto flex max-w-3xl items-end gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about airport investment opportunities..."
            rows={1}
            className="flex-1 resize-none overflow-hidden rounded-[var(--w-radius-card)] border border-border bg-surface-alt px-4 py-3 text-sm text-body placeholder-placeholder outline-none transition-colors focus:border-primary focus:ring-2 focus:ring-primary/20"
          />
          {sttSupported && (
            <button
              type="button"
              onClick={isListening ? stopListening : () => { if (isSpeaking) stopSpeaking(); startListening(); }}
              disabled={isLoading}
              aria-label={isListening ? "Stop recording" : "Start recording"}
              className={`rounded-full p-3 transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
                isListening
                  ? "bg-error text-white recording-pulse"
                  : "bg-surface-alt text-muted hover:text-heading hover:bg-primary-tint"
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
                {isListening ? (
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                ) : (
                  <>
                    <path d="M12 14a3 3 0 003-3V5a3 3 0 00-6 0v6a3 3 0 003 3z" />
                    <path d="M17 11a1 1 0 10-2 0 3 3 0 01-6 0 1 1 0 10-2 0 5 5 0 004 4.9V18H9a1 1 0 100 2h6a1 1 0 100-2h-2v-2.1A5 5 0 0017 11z" />
                  </>
                )}
              </svg>
            </button>
          )}
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-full bg-primary px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-primary-hover disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
