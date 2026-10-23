import type { Metadata, Viewport } from "next";
import {
  Bricolage_Grotesque,
  Fraunces,
  Geist_Mono,
  Instrument_Sans,
} from "next/font/google";
import { Footer } from "@/components/chrome/Footer";
import { Header } from "@/components/chrome/Header";
import { Providers } from "@/components/providers";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-bricolage",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const instrument = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-instrument",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Docgen — The Chroma Press",
    template: "%s · Docgen",
  },
  description:
    "Turn rough notes into compliance-grade, on-brand SOPs, setup guides and reports — with your wording untouched.",
  applicationName: "Docgen",
  keywords: ["Docgen", "SOP", "branded documents", "DOCX", "PDF", "Chroma Press"],
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F6F2EA" },
    { media: "(prefers-color-scheme: dark)", color: "#0B0B12" },
  ],
  colorScheme: "light dark",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${bricolage.variable} ${fraunces.variable} ${instrument.variable} ${geistMono.variable}`}
    >
      <body className="paper-atmosphere min-h-dvh antialiased">
        <Providers>
          <div className="relative flex min-h-dvh flex-col">
            <Header />
            <main className="relative z-10 flex-1">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
