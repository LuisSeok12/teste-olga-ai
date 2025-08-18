import fetch from "node-fetch";

const BASE = process.env.API_BASE || "http://127.0.0.1:3000";

export class QueueManager {
  async addToQueue(phone, message, priority = 5) {
    const r = await fetch(`${BASE}/api/queue/add`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ phone, message, priority })
    });
    if (!r.ok) throw new Error(`addToQueue failed: ${r.status}`);
    return r.json();
  }

  async getNext(batchSize = 5) {
    const r = await fetch(`${BASE}/api/queue/next`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ batchSize })
    });
    if (!r.ok) throw new Error(`getNext failed: ${r.status}`);
    return r.json();
  }

  async markCompleted(queueId, result) {
    const r = await fetch(`${BASE}/api/queue/${queueId}/complete`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(result || { status: "OK" })
    });
    if (!r.ok) throw new Error(`markCompleted failed: ${r.status}`);
    return r.json();
  }

  async markError(queueId, error) {
    const r = await fetch(`${BASE}/api/queue/${queueId}/error`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ error: String(error?.message || error || "unknown") })
    });
    if (!r.ok) throw new Error(`markError failed: ${r.status}`);
    return r.json();
  }
}
