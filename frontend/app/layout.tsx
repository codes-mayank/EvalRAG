import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = { title: "EvalRAG Documents", description: "Document ingestion and source extraction" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><header className="border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4"><Link href="/" className="text-xl font-bold tracking-tight text-slate-900">EvalRAG<span className="text-indigo-600">.</span></Link><span className="text-sm text-slate-500">Document ingestion</span></div></header>{children}</body></html>;
}
