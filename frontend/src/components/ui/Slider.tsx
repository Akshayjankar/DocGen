"use client";

import { cn } from "@/lib/cn";

interface SliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
  label?: string;
  className?: string;
}

export function Slider({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  label,
  className,
}: SliderProps) {
  return (
    <label className={cn("flex flex-col gap-2", className)}>
      {label ? (
        <span className="flex justify-between text-sm text-fg-muted">
          <span>{label}</span>
          <span className="font-mono text-fg">{value}</span>
        </span>
      ) : null}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-border accent-[var(--brand)]"
        aria-label={label}
      />
    </label>
  );
}
