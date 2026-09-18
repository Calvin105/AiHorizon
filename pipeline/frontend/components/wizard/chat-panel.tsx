"use client";

import * as React from "react";
import { Bot, ImagePlus, Send, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ChatMessage, ChipOption, PendingPrompt } from "@/components/wizard/chat-types";

/** Local pick-state, reset for free by remounting (parent keys this by
 * turn) rather than an effect that clears state on prop change. */
function ChipsMultiForm({
  options, maxPicks, confirmLabel, busy, onConfirm,
}: {
  options: ChipOption[];
  maxPicks?: number;
  confirmLabel: string;
  busy: boolean;
  onConfirm: (values: string[]) => void;
}) {
  const [picked, setPicked] = React.useState<string[]>([]);
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const active = picked.includes(o.value);
          return (
            <Button
              key={o.value} size="sm" disabled={busy}
              variant={active ? "default" : "outline"}
              onClick={() =>
                setPicked((prev) => {
                  if (active) return prev.filter((v) => v !== o.value);
                  const next = [...prev, o.value];
                  return maxPicks ? next.slice(-maxPicks) : next;
                })
              }
            >
              {o.label}
            </Button>
          );
        })}
      </div>
      <Button size="sm" disabled={busy || picked.length === 0} onClick={() => onConfirm(picked)}>
        {confirmLabel}
      </Button>
    </div>
  );
}

function TextForm({
  placeholder, confirmLabel, allowEmpty, busy, onSubmit,
}: {
  placeholder: string;
  confirmLabel: string;
  allowEmpty?: boolean;
  busy: boolean;
  onSubmit: (value: string) => void;
}) {
  const [value, setValue] = React.useState("");
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim() || allowEmpty) onSubmit(value.trim());
      }}
    >
      <Input autoFocus placeholder={placeholder} value={value} disabled={busy} onChange={(e) => setValue(e.target.value)} />
      <Button type="submit" size="icon" disabled={busy || (!value.trim() && !allowEmpty)} aria-label={confirmLabel}>
        <Send className="size-4" />
      </Button>
    </form>
  );
}

export function ChatPanel({
  messages, pending, busy, onChipSingle, onChipsMulti, onText, onPhoto, onSkip,
}: {
  messages: ChatMessage[];
  pending: PendingPrompt;
  busy: boolean;
  onChipSingle: (value: string) => void;
  onChipsMulti: (values: string[]) => void;
  onText: (value: string) => void;
  onPhoto: (file: File) => void;
  onSkip: () => void;
}) {
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  // Every new prompt follows at least one new message, so keying the input
  // area by the message count remounts it (and so resets any local pick/
  // text state) exactly when the prompt changes — no reset-on-prop effect.
  const turnKey = messages.length;

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-0 flex-1 overflow-y-scroll thin-scrollbar px-4">
        <div className="flex flex-col gap-4 py-4">
          {messages.map((m) => (
            <div key={m.id} className={`flex gap-2 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <Avatar className="size-7 shrink-0">
                <AvatarFallback>{m.role === "bot" ? <Bot className="size-4" /> : <User className="size-4" />}</AvatarFallback>
              </Avatar>
              <div
                className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                  m.role === "bot" ? "bg-muted" : "bg-primary text-primary-foreground"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}
          {busy && (
            <div className="flex gap-2">
              <Avatar className="size-7 shrink-0"><AvatarFallback><Bot className="size-4" /></AvatarFallback></Avatar>
              <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">…</div>
            </div>
          )}
          <div ref={bottomRef} />
          {/* Extra bottom space allowing scrolling with conversation items on top */}
          <div className="h-[45vh] shrink-0 pointer-events-none" aria-hidden="true" />
        </div>
      </div>

      <div className="border-t p-3">
        {pending.kind === "chips-single" && (
          <div className="flex flex-wrap gap-2">
            {pending.options.map((o) => (
              <Button key={o.value} variant="outline" size="sm" disabled={busy} onClick={() => onChipSingle(o.value)}>
                {o.label}
              </Button>
            ))}
          </div>
        )}

        {pending.kind === "chips-multi" && (
          <ChipsMultiForm
            key={turnKey} options={pending.options} maxPicks={pending.maxPicks}
            confirmLabel={pending.confirmLabel} busy={busy} onConfirm={onChipsMulti}
          />
        )}

        {pending.kind === "confirm" && (
          <div className="flex flex-wrap gap-2">
            {pending.options.map((o) => (
              <Button key={o.value} size="sm" disabled={busy} onClick={() => onChipSingle(o.value)}>
                {o.label}
              </Button>
            ))}
          </div>
        )}

        {pending.kind === "text" && (
          <TextForm
            key={turnKey} placeholder={pending.placeholder} confirmLabel={pending.confirmLabel}
            allowEmpty={pending.allowEmpty} busy={busy} onSubmit={onText}
          />
        )}

        {pending.kind === "text-with-suggestions" && (
          <div className="space-y-2">
            {pending.suggestions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {pending.suggestions.map((s) => (
                  <Button key={s.value} variant="outline" size="sm" disabled={busy} onClick={() => onText(s.label)}>
                    {s.label}
                  </Button>
                ))}
                <Button variant="ghost" size="sm" disabled={busy} onClick={onSkip}>
                  {pending.skipLabel}
                </Button>
              </div>
            )}
            <TextForm
              key={turnKey} placeholder={pending.placeholder} confirmLabel={pending.confirmLabel}
              allowEmpty={false} busy={busy} onSubmit={onText}
            />
          </div>
        )}

        {pending.kind === "photo-or-skip" && (
          <div className="flex items-center gap-2">
            <input
              ref={fileInputRef} type="file" accept="image/*" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) onPhoto(f); }}
            />
            <Button variant="outline" size="sm" disabled={busy} onClick={() => fileInputRef.current?.click()} className="gap-1.5">
              <ImagePlus className="size-4" /> Attach photo
            </Button>
            <Button variant="ghost" size="sm" disabled={busy} onClick={onSkip}>
              {pending.skipLabel}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
