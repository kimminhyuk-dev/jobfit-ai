'use client';

import { useEffect, useState } from 'react';
import Icon from './Icon';

export type ToastType = 'error' | 'success' | 'info';

export interface ToastPayload {
  type?: ToastType;
  message: string;
}

interface ToastItem extends ToastPayload {
  id: number;
}

const TOAST_EVENT = 'app:toast';
const AUTO_DISMISS_MS = 5000;

/** 어디서든(React 밖 포함) 토스트를 띄운다. */
export function showToast(message: string, type: ToastType = 'info') {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent<ToastPayload>(TOAST_EVENT, { detail: { type, message } }));
}

const STYLES: Record<ToastType, { bar: string; icon: 'x' | 'check' | 'bell' }> = {
  error: { bar: 'border-m-danger bg-m-danger-soft text-m-danger', icon: 'x' },
  success: { bar: 'border-m-success bg-m-success-soft text-m-success', icon: 'check' },
  info: { bar: 'border-m-border bg-m-surface text-m-text', icon: 'bell' },
};

export default function ToastHost() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    let counter = 0;
    function onToast(e: Event) {
      const detail = (e as CustomEvent<ToastPayload>).detail;
      if (!detail?.message) return;
      const id = ++counter;
      setToasts((prev) => [...prev, { id, type: detail.type ?? 'info', message: detail.message }]);
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, AUTO_DISMISS_MS);
    }
    window.addEventListener(TOAST_EVENT, onToast);
    return () => window.removeEventListener(TOAST_EVENT, onToast);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 w-[340px] max-w-[calc(100vw-2.5rem)]">
      {toasts.map((t) => {
        const style = STYLES[t.type ?? 'info'];
        return (
          <div
            key={t.id}
            role="alert"
            className={`flex items-start gap-2.5 rounded-xl border px-4 py-3 shadow-lg ${style.bar}`}
          >
            <Icon name={style.icon} size={16} className="mt-0.5 shrink-0" />
            <p className="flex-1 text-[13px] font-medium leading-snug break-words">{t.message}</p>
            <button
              onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))}
              className="shrink-0 opacity-60 hover:opacity-100"
              aria-label="닫기"
            >
              <Icon name="x" size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
