import type { Status } from "@/lib/api";

const styles: Record<Status, string> = {
  uploaded: "bg-slate-100 text-slate-700",
  processing: "bg-blue-100 text-blue-800",
  completed: "bg-emerald-100 text-emerald-800",
  failed: "bg-rose-100 text-rose-800",
};

export function StatusBadge({ status }: { status: Status }) {
  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold capitalize ${styles[status]}`}>{status}</span>;
}
