const state = {
  history: [],
  busy: false,
};

const FIXED_STRATEGY = "tool_calling";
const FIXED_PROVIDER = "deepseek";

const els = {
  kpiGpus: document.getElementById("kpi-gpus"),
  kpiVram: document.getElementById("kpi-vram"),
  gpuList: document.getElementById("gpu-list"),
  resetFleetBtn: document.getElementById("reset-fleet-btn"),
  clearChatBtn: document.getElementById("clear-chat-btn"),
  suggestions: document.getElementById("suggestions"),
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("empty-state"),
  chatForm: document.getElementById("chat-form"),
  messageInput: document.getElementById("message-input"),
  sendBtn: document.getElementById("send-btn"),
  themeToggleBtn: document.getElementById("theme-toggle-btn"),
  themeIcon: document.getElementById("theme-icon"),
  themeLabel: document.getElementById("theme-label"),
  modelBadgeText: document.getElementById("model-badge-text"),
  providerBadgeText: document.getElementById("provider-badge-text"),
};

const SUN_ICON = `<svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path></svg>`;
const MOON_ICON = `<svg class="icon icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInlineMarkdown(escaped) {
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdown(rawText) {
  const lines = escapeHtml(rawText).split("\n");
  const html = [];
  let inList = false;
  let tableRows = [];

  const flushList = () => {
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
  };

  const flushTable = () => {
    if (tableRows.length === 0) return;
    const rows = tableRows.filter((row) => !/^\s*\|?[\s:-]+\|/.test(row));
    if (rows.length > 0) {
      html.push("<table>");
      rows.forEach((row, idx) => {
        const cells = row
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((cell) => renderInlineMarkdown(cell.trim()));
        const tag = idx === 0 ? "th" : "td";
        html.push(`<tr>${cells.map((c) => `<${tag}>${c}</${tag}>`).join("")}</tr>`);
      });
      html.push("</table>");
    }
    tableRows = [];
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList();
      tableRows.push(trimmed);
      continue;
    }
    flushTable();

    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${renderInlineMarkdown(trimmed.replace(/^[-*]\s+/, ""))}</li>`);
      continue;
    }
    flushList();

    if (!trimmed) continue;
    html.push(`<p>${renderInlineMarkdown(trimmed)}</p>`);
  }

  flushList();
  flushTable();
  return html.join("");
}

async function fetchActiveModel() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) return;
    const data = await res.json();
    const provider = (data.providers || []).find((p) => p.name === FIXED_PROVIDER);
    if (els.providerBadgeText) {
      els.providerBadgeText.textContent = FIXED_PROVIDER;
    }
    if (provider && provider.default_model && els.modelBadgeText) {
      els.modelBadgeText.textContent = provider.default_model;
    }
  } catch {
    // Keep default badge label if config endpoint is unreachable
  }
}

async function fetchFleet() {
  const res = await fetch("/api/gpus");
  const data = await res.json();
  renderFleet(data.gpus, data.summary);
}

function renderFleet(gpus, summary) {
  els.kpiGpus.textContent = `${summary.available_gpus} / ${summary.total_gpus}`;
  els.kpiVram.textContent = `${summary.available_memory_gb} / ${summary.total_memory_gb} GB`;

  els.gpuList.innerHTML = "";
  for (const gpu of gpus) {
    const pct = gpu.total_quantity > 0
      ? Math.round((gpu.available_quantity / gpu.total_quantity) * 100)
      : 0;
    const fillClass = pct === 0 ? "empty" : pct <= 50 ? "low" : "";

    const card = document.createElement("div");
    card.className = "gpu-card";
    card.innerHTML = `
      <div class="gpu-card-top">
        <span class="gpu-name">${escapeHtml(gpu.name)}</span>
        <span class="vram-badge">${gpu.memory_gb} GB</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill ${fillClass}" style="width: ${pct}%"></div>
      </div>
      <div class="gpu-card-bottom">
        <span>${gpu.available_quantity} de ${gpu.total_quantity} disponíveis (${gpu.in_use_quantity} em uso)</span>
        <div class="stepper">
          <button type="button" data-action="dec" aria-label="Reduzir disponíveis de ${escapeHtml(gpu.name)}" ${gpu.available_quantity <= 0 ? "disabled" : ""}>−</button>
          <button type="button" data-action="inc" aria-label="Aumentar disponíveis de ${escapeHtml(gpu.name)}" ${gpu.available_quantity >= gpu.total_quantity ? "disabled" : ""}>+</button>
        </div>
      </div>
    `;

    card.querySelector('[data-action="dec"]').addEventListener("click", () => {
      updateAvailability(gpu.name, gpu.available_quantity - 1);
    });
    card.querySelector('[data-action="inc"]').addEventListener("click", () => {
      updateAvailability(gpu.name, gpu.available_quantity + 1);
    });
    els.gpuList.appendChild(card);
  }
}

async function updateAvailability(gpuName, nextQty) {
  const res = await fetch(`/api/gpus/${encodeURIComponent(gpuName)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ available_quantity: nextQty }),
  });
  if (res.ok) {
    await fetchFleet();
  }
}

function appendUserMessage(text) {
  if (els.emptyState) els.emptyState.style.display = "none";
  const div = document.createElement("div");
  div.className = "msg user";
  div.textContent = text;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function appendAssistantMessage(data) {
  const div = document.createElement("div");
  div.className = "msg assistant";

  const tools = data.tool_calls || [];
  let inspectorHtml = "";
  if (tools.length > 0) {
    const tracesHtml = tools
      .map(
        (tc) => `
          <div class="tool-trace">
            <div class="tool-trace-title">${escapeHtml(tc.name)}(${escapeHtml(JSON.stringify(tc.arguments))})</div>
            <pre>${escapeHtml(JSON.stringify(tc.result, null, 2))}</pre>
          </div>
        `
      )
      .join("");
    inspectorHtml = `
      <details class="tools-inspector">
        <summary>Inspecionar ${tools.length} tool call${tools.length > 1 ? "s" : ""}</summary>
        ${tracesHtml}
      </details>
    `;
  } else if (data.strategy === "prompt_stuffing") {
    inspectorHtml = `
      <div class="tools-inspector" style="color: var(--muted);">
        Snapshot SQLite injetado no system prompt (0 tool calls)
      </div>
    `;
  } else {
    inspectorHtml = `
      <div class="tools-inspector" style="color: var(--muted);">
        Nenhuma tool acionada neste turno
      </div>
    `;
  }

  div.innerHTML = `
    <div class="msg-content">${renderMarkdown(data.answer || "")}</div>
    <div class="telemetry">
      <span>strategy=${escapeHtml(data.strategy)}</span>
      <span>model=${escapeHtml(data.model)}</span>
      <span>calls=${data.llm_calls}</span>
      <span>${Math.round(data.latency_ms)} ms</span>
      <span>${data.total_tokens} tokens (${data.prompt_tokens} in / ${data.completion_tokens} out)</span>
    </div>
    ${inspectorHtml}
  `;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}

function appendErrorMessage(text) {
  const div = document.createElement("div");
  div.className = "msg error";
  div.textContent = text;
  els.messages.appendChild(div);
  els.messages.scrollTop = els.messages.scrollHeight;
}

async function sendMessage(text) {
  if (state.busy || !text.trim()) return;
  state.busy = true;
  els.sendBtn.disabled = true;
  els.sendBtn.classList.add("is-loading");

  appendUserMessage(text);
  els.messageInput.value = "";

  try {
    const payload = {
      message: text,
      history: state.history,
      strategy: FIXED_STRATEGY,
      provider: FIXED_PROVIDER,
    };

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      appendErrorMessage(`Erro (${res.status}): ${data.detail || "Falha ao processar mensagem."}`);
      return;
    }

    appendAssistantMessage(data);
    if (data.model && els.modelBadgeText) {
      els.modelBadgeText.textContent = data.model;
    }
    state.history.push({ role: "user", content: text });
    state.history.push({ role: "assistant", content: data.answer });
  } catch (err) {
    appendErrorMessage(`Erro de rede: ${err.message}`);
  } finally {
    state.busy = false;
    els.sendBtn.disabled = false;
    els.sendBtn.classList.remove("is-loading");
    els.messageInput.focus();
  }
}

els.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(els.messageInput.value);
});

els.suggestions.addEventListener("click", (event) => {
  const chip = event.target.closest(".chip");
  if (!chip) return;
  sendMessage(chip.dataset.prompt || "");
});

els.resetFleetBtn.addEventListener("click", async () => {
  const res = await fetch("/api/gpus/reset", { method: "POST" });
  if (res.ok) {
    const data = await res.json();
    renderFleet(data.gpus, data.summary);
  }
});

els.clearChatBtn.addEventListener("click", () => {
  state.history = [];
  els.messages.innerHTML = "";
  els.messages.appendChild(els.emptyState);
  els.emptyState.style.display = "block";
});

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  if (els.themeLabel) {
    els.themeLabel.textContent = theme === "light" ? "Tema escuro" : "Tema claro";
  }
  if (els.themeIcon) {
    els.themeIcon.innerHTML = theme === "light" ? MOON_ICON : SUN_ICON;
  }
  localStorage.setItem("gpu-fleet-theme", theme);
}

if (els.themeToggleBtn) {
  const savedTheme = localStorage.getItem("gpu-fleet-theme") || "dark";
  applyTheme(savedTheme);
  els.themeToggleBtn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
  });
}

Promise.all([fetchActiveModel(), fetchFleet()]).catch((err) => {
  appendErrorMessage(`Falha ao carregar dados iniciais: ${err.message}`);
});
