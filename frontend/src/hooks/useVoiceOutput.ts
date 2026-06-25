import { useState, useRef, useEffect, useCallback } from "react";

interface UseVoiceOutputReturn {
  isSpeaking: boolean;
  speak: (text: string) => void;
  stop: () => void;
  isSupported: boolean;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/#{1,6}\s+/g, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^\|.*\|$/gm, "")
    .replace(/^[\s|:-]+$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function useVoiceOutput(): UseVoiceOutputReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const keepAliveRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setIsSupported(
      typeof window !== "undefined" && "speechSynthesis" in window
    );
  }, []);

  const clearKeepAlive = useCallback(() => {
    if (keepAliveRef.current) {
      clearInterval(keepAliveRef.current);
      keepAliveRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    clearKeepAlive();
  }, [clearKeepAlive]);

  const speak = useCallback(
    (text: string) => {
      window.speechSynthesis.cancel();
      clearKeepAlive();

      const cleaned = stripMarkdown(text);
      if (!cleaned) return;

      const utterance = new SpeechSynthesisUtterance(cleaned);
      utterance.lang = "en-US";

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        clearKeepAlive();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        clearKeepAlive();
      };

      // Chrome pauses long utterances — periodic pause/resume keeps it alive
      keepAliveRef.current = setInterval(() => {
        if (window.speechSynthesis.speaking) {
          window.speechSynthesis.pause();
          window.speechSynthesis.resume();
        }
      }, 10_000);

      window.speechSynthesis.speak(utterance);
    },
    [clearKeepAlive]
  );

  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      clearKeepAlive();
    };
  }, [clearKeepAlive]);

  return { isSpeaking, speak, stop, isSupported };
}
