export type Status = "uploaded" | "processing" | "completed" | "failed";

export interface Document {
  id: string;
  filename: string;
  content_hash: string;
  file_size: number;
  page_count: number;
  status: Status;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document { passage_count: number }
export interface Passage {
  id: string;
  page_number: number;
  block_index: number;
  text: string;
  start_char: number;
  end_char: number;
}
export interface DocumentList { items: Document[]; total: number; page: number; page_size: number }
export interface PageResult { document_id: string; page_number: number; blocks: Passage[] }

const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, { cache: "no-store", ...options });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { detail = (await response.json()).detail ?? detail; } catch { /* non-JSON error */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const api = {
  documents: (page = 1) => request<DocumentList>(`/documents?page=${page}&page_size=20`),
  document: (id: string) => request<DocumentDetail>(`/documents/${id}`),
  page: (id: string, page: number) => request<PageResult>(`/documents/${id}/pages/${page}`),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<Document>("/documents", { method: "POST", body });
  },
};
