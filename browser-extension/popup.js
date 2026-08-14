const ports = [8001, 8000];
let capturedPage = null;
let apiBase = null;

const status = document.querySelector("#status");
const emptyState = document.querySelector("#empty-state");
const previewState = document.querySelector("#preview-state");
const fields = ["title", "company", "city", "salary", "experience", "education"];

function setStatus(message, isError = false) {
  status.textContent = message;
  status.style.color = isError ? "#a33b32" : "#60708d";
}

async function findApiBase() {
  for (const port of ports) {
    const candidate = `http://127.0.0.1:${port}`;
    try {
      const response = await fetch(`${candidate}/health`);
      if (response.ok) return candidate;
    } catch (_) {
      // Try the other local Pathlight mode.
    }
  }
  throw new Error("未找到 Pathlight 本机服务。请先启动桌面应用或本地开发服务。");
}

async function readCurrentPage() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.includes("zhipin.com")) {
    throw new Error("请先切换到一个 BOSS 职位详情页。");
  }
  const page = await chrome.tabs.sendMessage(tab.id, { type: "pathlight:read-visible-job" });
  if (!page?.visible_text || page.visible_text.length < 30) {
    throw new Error("当前页面没有足够的可见职位内容，请等待页面加载完成后再试。");
  }
  return page;
}

function setPreview(preview) {
  for (const field of fields) document.querySelector(`#${field}`).value = preview[field] || "";
  document.querySelector("#excerpt").value = preview.jd_excerpt;
  document.querySelector("#source").textContent = preview.source_link;
  emptyState.classList.add("hidden");
  previewState.classList.remove("hidden");
}

document.querySelector("#capture").addEventListener("click", async () => {
  try {
    setStatus("正在读取当前可见职位内容…");
    capturedPage = await readCurrentPage();
    apiBase = await findApiBase();
    const response = await fetch(`${apiBase}/api/bridge/job-preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(capturedPage),
    });
    const preview = await response.json();
    if (!response.ok) throw new Error(preview.detail || "无法生成职位预览。");
    setPreview(preview);
    setStatus("请检查字段，再确认导入。");
  } catch (error) {
    setStatus(error.message || "读取失败。", true);
  }
});

document.querySelector("#confirm").addEventListener("click", async () => {
  if (!capturedPage || !apiBase) return;
  const button = document.querySelector("#confirm");
  button.disabled = true;
  try {
    const overrides = Object.fromEntries(fields.map((field) => [field, document.querySelector(`#${field}`).value.trim()]));
    const response = await fetch(`${apiBase}/api/bridge/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...capturedPage, ...overrides }),
    });
    const job = await response.json();
    if (!response.ok) throw new Error(job.detail || "导入失败。");
    setStatus(`已导入“${job.title || "未命名职位"}”，现在可在 Pathlight 的岗位分析页校对。`);
  } catch (error) {
    setStatus(error.message || "导入失败。", true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#restart").addEventListener("click", () => {
  previewState.classList.add("hidden");
  emptyState.classList.remove("hidden");
  capturedPage = null;
  setStatus("");
});
