// Mock de análise de fraude (standalone)
export function fraudScore(payload) {
  // regras bobas só para demonstrar
  let score = 10;
  if (/urgente/i.test(payload?.message)) score += 20;
  if (/batida/i.test(payload?.message)) score += 15;
  return Math.min(score, 100);
}
