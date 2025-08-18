import fetch from "node-fetch";
const BASE = process.env.API_BASE || "http://127.0.0.1:3000";

export class CustomerRouter {
  async routeCustomer(phone, message) {
    const r = await fetch(`${BASE}/api/router/route`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ phone, message })
    });
    if (!r.ok) throw new Error(`routeCustomer failed: ${r.status}`);
    return r.json();
  }
}
