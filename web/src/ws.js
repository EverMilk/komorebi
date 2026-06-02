// Thin WebSocket client. Knows nothing about rendering — it just connects, sends
// JSON frames, and dispatches incoming messages by their `type` to handlers.

export class KomorebiSocket {
  constructor(url) {
    this.url = url;
    this.handlers = new Map(); // type -> fn(msg)
    this.ws = null;
  }

  on(type, fn) {
    this.handlers.set(type, fn);
    return this;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.addEventListener("message", (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      const fn = this.handlers.get(msg.type);
      if (fn) fn(msg);
    });
    return new Promise((resolve, reject) => {
      this.ws.addEventListener("open", () => resolve(this));
      this.ws.addEventListener("error", reject);
    });
  }

  send(obj) {
    this.ws?.send(JSON.stringify(obj));
  }

  close() {
    try {
      this.ws?.close();
    } catch {
      /* already closed */
    }
    this.ws = null;
  }
}
