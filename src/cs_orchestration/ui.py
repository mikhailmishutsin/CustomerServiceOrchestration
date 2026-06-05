from fastapi.responses import HTMLResponse


def render_agent_preview(*, integration_mode: str, dry_run: bool) -> HTMLResponse:
    api_mode = "Real Order Business API" if integration_mode == "real" else "Mock OMS"
    update_mode = "Dry run" if dry_run else "Live update"
    sample = _sample_values(enabled=integration_mode != "real")
    html = _HTML.replace("{{STATUS_TEXT}}", f"{api_mode} · {update_mode}")
    for key, value in sample.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return HTMLResponse(html)


def _sample_values(*, enabled: bool) -> dict[str, str]:
    if not enabled:
        return {
            "TICKET_ID": "",
            "CUSTOMER_NAME": "",
            "CUSTOMER_EMAIL": "",
            "CUSTOMER_PHONE": "",
            "SUBJECT": "",
            "DESCRIPTION": "",
        }
    return {
        "TICKET_ID": "12345",
        "CUSTOMER_NAME": "John Customer",
        "CUSTOMER_EMAIL": "customer@example.com",
        "CUSTOMER_PHONE": "+15555555555",
        "SUBJECT": "Where is my order?",
        "DESCRIPTION": "I need an update on delivery",
    }


_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Customer Service Orchestration</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f6f7f9;
        --panel: #ffffff;
        --text: #17202a;
        --muted: #687385;
        --line: #d9dee7;
        --accent: #1f6feb;
        --accent-dark: #1557bd;
        --ok: #1f7a4d;
        --warn: #a15c00;
        --shadow: 0 8px 24px rgba(23, 32, 42, 0.08);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 15px;
        letter-spacing: 0;
      }

      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
        min-height: 64px;
        padding: 0 28px;
        border-bottom: 1px solid var(--line);
        background: var(--panel);
      }

      h1 {
        margin: 0;
        font-size: 18px;
        font-weight: 650;
      }

      .status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: var(--muted);
        font-size: 13px;
      }

      .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--ok);
      }

      main {
        display: grid;
        grid-template-columns: minmax(320px, 460px) minmax(0, 1fr);
        gap: 20px;
        padding: 20px;
        max-width: 1380px;
        margin: 0 auto;
      }

      section {
        min-width: 0;
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
      }

      .panel-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        min-height: 52px;
        padding: 0 18px;
        border-bottom: 1px solid var(--line);
      }

      h2 {
        margin: 0;
        font-size: 15px;
        font-weight: 650;
      }

      form {
        display: grid;
        gap: 14px;
        padding: 18px;
      }

      .grid-two {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
      }

      label {
        display: grid;
        gap: 6px;
        color: var(--muted);
        font-size: 12px;
        font-weight: 600;
      }

      input,
      select,
      textarea {
        width: 100%;
        min-height: 38px;
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 9px 10px;
        color: var(--text);
        background: #fff;
        font: inherit;
      }

      textarea {
        min-height: 92px;
        resize: vertical;
      }

      input:focus,
      select:focus,
      textarea:focus {
        outline: 2px solid rgba(31, 111, 235, 0.22);
        border-color: var(--accent);
      }

      button {
        width: 100%;
        min-height: 42px;
        border: 0;
        border-radius: 6px;
        background: var(--accent);
        color: #fff;
        font: inherit;
        font-weight: 650;
        cursor: pointer;
      }

      button:hover {
        background: var(--accent-dark);
      }

      button:disabled {
        cursor: wait;
        opacity: 0.65;
      }

      .result {
        display: grid;
        gap: 16px;
        padding: 18px;
      }

      .summary-line {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .pill {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border-radius: 999px;
        background: #eef3fb;
        color: #20344f;
        font-size: 13px;
        font-weight: 600;
      }

      .pill.ok {
        background: #e9f7ef;
        color: var(--ok);
      }

      .pill.warn {
        background: #fff5e5;
        color: var(--warn);
      }

      .note {
        min-height: 300px;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        padding: 14px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #fbfcfe;
        line-height: 1.55;
      }

      .facts {
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      }

      .fact {
        min-height: 72px;
        padding: 12px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #fbfcfe;
      }

      .fact-label {
        margin-bottom: 6px;
        color: var(--muted);
        font-size: 12px;
        font-weight: 600;
      }

      .fact-value {
        color: var(--text);
        font-size: 14px;
        font-weight: 600;
        overflow-wrap: anywhere;
      }

      .fact-value a {
        color: var(--accent);
        text-decoration: none;
      }

      .fact-value a:hover {
        text-decoration: underline;
      }

      .json {
        max-height: 280px;
        overflow: auto;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        padding: 14px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #111827;
        color: #e5e7eb;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 12px;
        line-height: 1.5;
      }

      .empty {
        color: var(--muted);
      }

      @media (max-width: 880px) {
        header {
          align-items: flex-start;
          flex-direction: column;
          justify-content: center;
          padding: 14px 18px;
        }

        main {
          grid-template-columns: 1fr;
          padding: 14px;
        }

        .grid-two {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <header>
      <h1>Customer Service Orchestration</h1>
      <div class="status"><span class="dot"></span><span>{{STATUS_TEXT}}</span></div>
    </header>

    <main>
      <section>
        <div class="panel-head">
          <h2>Ticket</h2>
        </div>
        <form id="ticket-form">
          <div class="grid-two">
            <label>
              Ticket ID
              <input id="ticket_id" value="{{TICKET_ID}}" autocomplete="off">
            </label>
            <label>
              Channel
              <select id="channel">
                <option value="freshdesk">Freshdesk</option>
                <option value="email">Email</option>
                <option value="chat">Chat</option>
                <option value="marketplace">Marketplace</option>
              </select>
            </label>
          </div>

          <label>
            Customer name
            <input id="customer_name" value="{{CUSTOMER_NAME}}" autocomplete="off">
          </label>

          <div class="grid-two">
            <label>
              Email
              <input id="customer_email" value="{{CUSTOMER_EMAIL}}" autocomplete="off">
            </label>
            <label>
              Phone
              <input id="customer_phone" value="{{CUSTOMER_PHONE}}" autocomplete="off">
            </label>
          </div>

          <label>
            Subject
            <input id="subject" value="{{SUBJECT}}" autocomplete="off">
          </label>

          <label>
            Description
            <textarea id="description">{{DESCRIPTION}}</textarea>
          </label>

          <button id="submit-button" type="submit">Enrich ticket</button>
        </form>
      </section>

      <section>
        <div class="panel-head">
          <h2>Result</h2>
        </div>
        <div class="result">
          <div id="summary" class="summary-line">
            <span class="pill">Ready</span>
          </div>
          <div>
            <h2>Latest order</h2>
            <div id="facts" class="facts">
              <div class="fact"><div class="fact-label">Delivery status</div><div class="fact-value empty">No enrichment run yet.</div></div>
              <div class="fact"><div class="fact-label">ETA</div><div class="fact-value empty">No enrichment run yet.</div></div>
              <div class="fact"><div class="fact-label">Order date</div><div class="fact-value empty">No enrichment run yet.</div></div>
              <div class="fact"><div class="fact-label">Sales order</div><div class="fact-value empty">No enrichment run yet.</div></div>
            </div>
          </div>
          <div>
            <h2>Private note</h2>
            <div id="private-note" class="note empty">No enrichment run yet.</div>
          </div>
          <div>
            <h2>Payload</h2>
            <pre id="payload" class="json">{}</pre>
          </div>
          <div>
            <h2>Debug</h2>
            <pre id="debug" class="json">{}</pre>
          </div>
        </div>
      </section>
    </main>

    <script>
      const form = document.getElementById("ticket-form");
      const button = document.getElementById("submit-button");
      const summary = document.getElementById("summary");
      const facts = document.getElementById("facts");
      const privateNote = document.getElementById("private-note");
      const payload = document.getElementById("payload");
      const debug = document.getElementById("debug");

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        button.disabled = true;
        button.textContent = "Enriching...";
        summary.innerHTML = '<span class="pill">Running</span>';

        const request = {
          ticket_id: value("ticket_id"),
          customer: {
            name: value("customer_name"),
            email: value("customer_email"),
            phone: value("customer_phone"),
          },
          ticket: {
            subject: value("subject"),
            description: value("description"),
            source: "agent-preview",
            channel: value("channel"),
          },
        };
        renderDebug(request, {});

        try {
          const response = await fetch("/enrich-ticket", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(request),
          });
          const body = await parseResponse(response);
          if (!response.ok) {
            throw { message: errorMessage(body), body };
          }
          renderResult(body, request);
        } catch (error) {
          summary.innerHTML = '<span class="pill warn">Error</span>';
          privateNote.classList.remove("empty");
          privateNote.textContent = error.message;
          payload.textContent = JSON.stringify(error.body || {}, null, 2);
          renderDebug(request, error.body || {});
        } finally {
          button.disabled = false;
          button.textContent = "Enrich ticket";
        }
      });

      function renderResult(body, request) {
        const warnings = body.metadata?.warnings || [];
        summary.innerHTML = `
          <span class="pill ok">${body.metadata?.confidence || "unknown"} confidence</span>
          <span class="pill">${body.metadata?.order_count ?? 0} order(s)</span>
          <span class="pill">${body.metadata?.dry_run ? "Dry run" : "Live update"}</span>
          ${warnings.length ? '<span class="pill warn">Warnings</span>' : ""}
        `;
        privateNote.classList.remove("empty");
        privateNote.textContent = body.private_note || "";
        renderFacts(body);
        payload.textContent = JSON.stringify(body, null, 2);
        renderDebug(request, body);
      }

      function renderFacts(body) {
        const fields = body.custom_fields || {};
        facts.innerHTML = `
          ${factCard("Delivery status", fields.delivery_status || "Unavailable")}
          ${factCard("ETA", fields.delivery_eta || "Unavailable")}
          ${factCard("Order date", fields.order_date || "Unavailable")}
          ${factCard("Sales order", orderLinkMarkup(fields.order_link))}
        `;
      }

      function factCard(label, valueMarkup) {
        return `
          <div class="fact">
            <div class="fact-label">${escapeHtml(label)}</div>
            <div class="fact-value">${valueMarkup}</div>
          </div>
        `;
      }

      function orderLinkMarkup(url) {
        if (!url) {
          return "Unavailable";
        }
        return `<a href="${escapeAttribute(url)}" target="_blank" rel="noreferrer">Open SO</a>`;
      }

      function value(id) {
        return document.getElementById(id).value.trim();
      }

      async function parseResponse(response) {
        const text = await response.text();
        if (!text) {
          return {};
        }
        try {
          return JSON.parse(text);
        } catch {
          return { detail: text };
        }
      }

      function errorMessage(body) {
        if (typeof body.detail?.message === "string") {
          return body.detail.message;
        }
        if (typeof body.detail === "string") {
          return body.detail;
        }
        return JSON.stringify(body, null, 2);
      }

      function renderDebug(browserRequest, responseBody) {
        const responseDebug = responseBody.detail?.debug || responseBody.metadata?.debug || {};
        debug.textContent = JSON.stringify({
          browser_request: {
            method: "POST",
            url: "/enrich-ticket",
            body: browserRequest,
          },
          backend_request: responseDebug.order_business_request || null,
        }, null, 2);
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      function escapeAttribute(value) {
        return escapeHtml(value);
      }
    </script>
  </body>
</html>
"""
