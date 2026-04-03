export function formatTime(isoString: string): string {
  const d = new Date(isoString);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function formatBP(systolic?: number, diastolic?: number): string {
  if (systolic == null || diastolic == null) return '—';
  return `${systolic}/${diastolic}`;
}

export function formatDuration(startIso: string): string {
  const diffMs = Date.now() - new Date(startIso).getTime();
  const totalSec = Math.floor(diffMs / 1000);
  const mins = Math.floor(totalSec / 60).toString().padStart(2, '0');
  const secs = (totalSec % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
}
