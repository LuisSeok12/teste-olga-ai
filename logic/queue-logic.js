
export function rankQueue(items) {
  // priority menor → mais urgente
  return [...items].sort((a, b) =>
    a.priority - b.priority || new Date(a.created_at) - new Date(b.created_at)
  );
}
export function estimateWait(position, avgSeconds = 60) {
  const mins = Math.ceil((position * avgSeconds) / 60);
  return `${mins} minutos`;
}
