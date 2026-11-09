"use client";

import { ChangeEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, FileText, UploadCloud } from "lucide-react";
import { api, DocumentList } from "@/lib/api";
import { StatusBadge } from "@/components/status-badge";

function size(bytes: number) { return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`; }

export default function Dashboard() {
  const [data, setData] = useState<DocumentList | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try { setData(await api.documents(page)); setError(""); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load documents"); }
    finally { setLoading(false); }
  }, [page]);
  useEffect(() => { void load(); }, [load]);

  async function onUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try { await api.upload(file); setPage(1); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Upload failed"); await load(); }
    finally { setUploading(false); event.target.value = ""; }
  }

  return <main className="mx-auto max-w-6xl px-6 py-12">
    <div className="mb-10 flex flex-wrap items-end justify-between gap-6">
      <div><p className="mb-2 text-sm font-semibold uppercase tracking-widest text-indigo-600">Library</p><h1 className="text-3xl font-bold tracking-tight">Documents</h1><p className="mt-2 text-slate-600">Upload PDFs and inspect their extracted source text.</p></div>
      <label className={`inline-flex cursor-pointer items-center gap-2 rounded-lg bg-indigo-600 px-5 py-3 font-medium text-white shadow-sm hover:bg-indigo-700 ${uploading ? "opacity-60" : ""}`}><UploadCloud size={18} />{uploading ? "Processing…" : "Upload PDF"}<input className="sr-only" type="file" accept="application/pdf,.pdf" disabled={uploading} onChange={onUpload} /></label>
    </div>
    {error && <div role="alert" className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-800">{error}</div>}
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-4 text-sm font-medium text-slate-600">{data ? `${data.total} document${data.total === 1 ? "" : "s"}` : "Documents"}</div>
      {loading ? <p className="p-12 text-center text-slate-500">Loading documents…</p> : data?.items.length ? <div className="divide-y divide-slate-100">{data.items.map((doc) => <Link key={doc.id} href={`/documents/${doc.id}`} className="flex items-center gap-4 px-6 py-5 hover:bg-slate-50"><div className="rounded-lg bg-indigo-50 p-3 text-indigo-600"><FileText size={22} /></div><div className="min-w-0 flex-1"><p className="truncate font-semibold">{doc.filename}</p><p className="mt-1 text-sm text-slate-500">{size(doc.file_size)} · {doc.page_count} pages · {new Date(doc.created_at).toLocaleDateString()}</p></div><StatusBadge status={doc.status} /><ArrowRight className="text-slate-400" size={18} /></Link>)}</div> : <div className="p-16 text-center"><FileText className="mx-auto mb-4 text-slate-300" size={38} /><p className="font-medium">No documents yet</p><p className="mt-1 text-sm text-slate-500">Upload a PDF to see its extracted pages here.</p></div>}
      {data && data.total > data.page_size && <div className="flex items-center justify-between border-t border-slate-200 px-6 py-4 text-sm"><button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button><span>Page {page} of {Math.ceil(data.total / data.page_size)}</span><button disabled={page * data.page_size >= data.total} onClick={() => setPage(page + 1)}>Next</button></div>}
    </section>
  </main>;
}
