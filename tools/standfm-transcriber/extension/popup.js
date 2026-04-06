const SERVER = "http://localhost:5555";
let currentResult = null;
let currentUrl = "";

const $ = (s) => document.getElementById(s);

function showView(id) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  $(id).classList.remove("hidden");
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2000);
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}分${s}秒`;
}

function formatDate(ts) {
  const d = new Date(ts);
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

async function checkServer() {
  try {
    const r = await fetch(`${SERVER}/health`, { signal: AbortSignal.timeout(2000) });
    return r.ok;
  } catch {
    return false;
  }
}

async function fetchEpisodeInfo(episodeId) {
  const r = await fetch(`https://stand.fm/api/episodes/${episodeId}`);
  const data = await r.json();
  const ep = data.response.episodes[episodeId];
  const topics = data.response.topics || {};
  let audioUrl = null;
  for (const t of Object.values(topics)) {
    if (t.episodeId === episodeId) {
      audioUrl = t.downloadUrl;
      break;
    }
  }
  return {
    title: ep.title,
    duration: ep.totalDuration / 1000,
    date: ep.publishedAt || ep.createdAt,
    audioUrl,
  };
}

async function startTranscription(url) {
  showView("view-progress");
  $("prog-title").textContent = $("ep-title").textContent;
  $("prog-status").textContent = "サーバーに接続中...";
  $("prog-sub").textContent = "";

  try {
    const resp = await fetch(`${SERVER}/transcribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.error || "サーバーエラー");
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const data = JSON.parse(line);
          handleStreamEvent(data);
        } catch {
          // skip malformed lines
        }
      }
    }

    if (buffer.trim()) {
      try {
        handleStreamEvent(JSON.parse(buffer));
      } catch {
        // skip
      }
    }
  } catch (e) {
    showError(
      e.message.includes("Failed to fetch")
        ? "サーバーに接続できません。サーバーが起動しているか確認してください。"
        : e.message
    );
  }
}

function handleStreamEvent(data) {
  switch (data.status) {
    case "info":
    case "downloading":
    case "converting":
    case "transcribing":
      $("prog-status").textContent = data.message;
      if (data.title) $("prog-title").textContent = data.title;
      if (data.status === "transcribing") {
        $("prog-sub").textContent = "音声の長さによって数分かかることがあります";
      }
      break;

    case "done":
      currentResult = data;
      showResult(data);
      break;

    case "error":
      showError(data.message);
      break;
  }
}

function showResult(data) {
  showView("view-result");
  $("res-title").textContent = data.title;
  $("res-meta").textContent = `${formatDuration(data.duration)} の音声`;
  $("res-text").textContent = data.text;
}

function showError(msg) {
  showView("view-error");
  $("error-content").innerHTML = `<strong>エラーが発生しました</strong>${msg}`;
}

async function copyToClipboard() {
  if (!currentResult) return;
  try {
    await navigator.clipboard.writeText(currentResult.text);
    toast("コピーしました");
  } catch {
    toast("コピーに失敗しました");
  }
}

async function saveToObsidian() {
  if (!currentResult) return;
  const folder = $("save-folder").value.trim() || "brain";
  try {
    const r = await fetch(`${SERVER}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: currentResult.title,
        text: currentResult.text,
        url: currentResult.url,
        duration: currentResult.duration,
        folder,
      }),
    });
    const data = await r.json();
    if (data.status === "ok") {
      toast(`保存しました: ${data.path}`);
    } else {
      toast("保存に失敗しました");
    }
  } catch {
    toast("サーバーに接続できません");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab?.url || "";
  currentUrl = url;

  const match = url.match(/stand\.fm\/episodes\/([a-f0-9]+)/);
  if (!match) {
    showView("view-not-supported");
    return;
  }

  const episodeId = match[1];

  try {
    const [info, serverOk] = await Promise.all([
      fetchEpisodeInfo(episodeId),
      checkServer(),
    ]);

    $("ep-title").textContent = info.title;
    $("ep-duration").textContent = formatDuration(info.duration);
    $("ep-date").textContent = formatDate(info.date);
    showView("view-episode");

    if (!serverOk) {
      $("server-warn").classList.remove("hidden");
      $("btn-transcribe").disabled = true;
    }
  } catch (e) {
    showError(`エピソード情報の取得に失敗しました: ${e.message}`);
  }

  $("btn-transcribe").addEventListener("click", () => startTranscription(url));
  $("btn-copy").addEventListener("click", copyToClipboard);
  $("btn-save").addEventListener("click", saveToObsidian);
  $("btn-retry").addEventListener("click", () => {
    showView("view-episode");
    checkServer().then((ok) => {
      if (ok) {
        $("server-warn").classList.add("hidden");
        $("btn-transcribe").disabled = false;
      }
    });
  });
});
