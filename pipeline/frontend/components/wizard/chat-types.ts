export interface ChatMessage {
  id: string;
  role: "bot" | "user";
  text: string;
}

export interface ChipOption {
  value: string;
  label: string;
  helpText?: string;
}

/** What the input area at the bottom of the chat currently expects. */
export type PendingPrompt =
  | { kind: "chips-single"; options: ChipOption[] }
  | { kind: "chips-multi"; options: ChipOption[]; maxPicks?: number; confirmLabel: string }
  | { kind: "text"; placeholder: string; confirmLabel: string; allowEmpty?: boolean }
  | {
      kind: "text-with-suggestions";
      suggestions: ChipOption[];
      placeholder: string;
      confirmLabel: string;
      skipLabel: string;
    }
  | { kind: "photo-or-skip"; skipLabel: string }
  | { kind: "confirm"; options: ChipOption[] }
  | { kind: "none" };

let counter = 0;
export function nextId(): string {
  counter += 1;
  return `m${counter}`;
}
