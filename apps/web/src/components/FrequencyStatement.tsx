export interface FrequencyStatementProps {
  intervalMs: number;
}

function formatInterval(intervalMs: number): { value: number; unit: string } {
  const seconds = Math.round(intervalMs / 1000);
  if (seconds < 60) {
    return { value: seconds, unit: seconds === 1 ? "second" : "seconds" };
  }
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return { value: minutes, unit: minutes === 1 ? "minute" : "minutes" };
  }
  const hours = Math.round(minutes / 60);
  if (hours < 24) {
    return { value: hours, unit: hours === 1 ? "hour" : "hours" };
  }
  const days = Math.round(hours / 24);
  return { value: days, unit: days === 1 ? "day" : "days" };
}

export function FrequencyStatement({ intervalMs }: FrequencyStatementProps) {
  const { value, unit } = formatInterval(intervalMs);

  return (
    <span className="text-sm text-slate-400">
      Updated every {value} {unit}
    </span>
  );
}
