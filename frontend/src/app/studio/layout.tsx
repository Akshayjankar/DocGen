import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Studio",
  description: "Three-pane Docgen workspace — source, paper, theme.",
};

export default function StudioLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
