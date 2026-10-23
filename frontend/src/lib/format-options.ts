import type { DocType } from "@/types/api";

export const FORMAT_OPTIONS: { id: DocType; label: string; hint?: string }[] = [
  { id: "sop", label: "SOP", hint: "Procedures" },
  { id: "setup_guide", label: "Setup guide", hint: "How-to" },
  { id: "report", label: "Report", hint: "Findings" },
  { id: "policy", label: "Policy", hint: "Governance" },
  { id: "release_notes", label: "Release notes", hint: "Ship log" },
  { id: "proposal", label: "Proposal", hint: "Pitch" },
  { id: "meeting_minutes", label: "Minutes", hint: "Meetings" },
  { id: "memo", label: "Memo", hint: "Internal note" },
];
