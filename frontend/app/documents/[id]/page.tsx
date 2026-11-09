"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ChevronLeft, ChevronRight, FileText } from "lucide-react";
import { api, DocumentDetail, PageResult } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";

export default function Details({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [page, setPage] = useState<PageResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api.document(id).then((result) => { if (active) { setDocument(result); setError(""); } }).catch((err) => { if (active) setError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);

  useEffect(() => {
    if (!document || document.status !== "completed") return;
    let active = true;
    setPage(null);
    api.page(id, pageNumber).then((result) => { if (active) { setPage(result); setError(""); } }).catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [id, pageNumber, document]);

  return <main className="mx-auto max-w-4xl px-6 py-12"><Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-indigo-600"><ArrowLeft size={16} />All documents</Link>
    {error && <div role="alert" className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-800">{error}</div>}
    {loading ? <p className="text-slate-500">Loading document…</p> : document && <>
      <div className="mb-8 rounded-xl border border-slate-200 bg-white p-7 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex min-w-0 items-center gap-4"><div className="rounded-xl bg-indigo-50 p-4 text-indigo-600"><FileText size={28} /></div><div className="min-w-0"><h1 className="truncate text-2xl font-bold">{document.filename}</h1><p className="mt-1 text-sm text-slate-500">Uploaded {new Date(document.created_at).toLocaleString()}</p></div></div><StatusBadge status={document.status} /></div>
      <dl className="mt-8 grid grid-cols-2 gap-6 border-t border-slate-100 pt-6 text-sm sm:grid-cols-4"><div><dt className="text-slate-500">Size</dt><dd className="mt-1 font-semibold">{(document.file_size / 1024).toFixed(1)} KB</dd></div><div><dt className="text-slate-500">Pages</dt><dd className="mt-1 font-semibold">{document.page_count}</dd></div><div><dt className="text-slate-500">Text blocks</dt><dd className="mt-1 font-semibold">{document.passage_count}</dd></div><div><dt className="text-slate-500">SHA-256</dt><dd className="mt-1 truncate font-mono text-xs" title={document.content_hash}>{document.content_hash.slice(0, 12)}…</dd></div></dl></div>
      {document.status === "failed" ? <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-rose-800"><h2 className="font-semibold">Text extraction failed</h2><p className="mt-2 text-sm">{document.error_message ?? "This PDF could not be processed."}</p></div> : document.status !== "completed" ? <p className="rounded-xl bg-blue-50 p-6 text-blue-800">This document is being processed.</p> : <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-200 px-6 py-4"><h2 className="font-semibold">Extracted text</h2><div className="flex items-center gap-4 text-sm"><button aria-label="Previous page" disabled={pageNumber <= 1} onClick={() => setPageNumber(pageNumber - 1)}><ChevronLeft size={20} /></button><span>Page {pageNumber} of {document.page_count}</span><button aria-label="Next page" disabled={pageNumber >= document.page_count} onClick={() => setPageNumber(pageNumber + 1)}><ChevronRight size={20} /></button></div></div><div className="space-y-5 p-6">{!page ? <p className="text-slate-500">Loading page…</p> : page.blocks.length ? page.blocks.map((block) => <div key={block.id} className="rounded-lg border border-slate-100 bg-slate-50 p-4"><p className="whitespace-pre-wrap leading-7 text-slate-800">{block.text}</p><p className="mt-3 text-xs text-slate-400">Block {block.block_index + 1} · characters {block.start_char}–{block.end_char}</p></div>) : <p className="text-slate-500">No selectable text on this page.</p>}</div></section>}
    </>}
  </main>;
}
