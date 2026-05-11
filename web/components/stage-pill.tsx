import clsx from "clsx";

const STATUS_TONE: Record<string, string> = {
  completed: "bg-success/15 text-success border-success/30",
  in_progress: "bg-amber-whisper text-amber border-amber/40",
  pending: "bg-mist text-charcoal border-mist",
  failed: "bg-danger/15 text-danger border-danger/30",
  skipped: "bg-ash/20 text-ash border-ash/30",
};

export function StagePill({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 text-micro-label uppercase rounded-sm border",
        STATUS_TONE[status] ?? "bg-mist text-charcoal border-mist",
      )}
    >
      {status.replace("_", " ")}
    </span>
  );
}
