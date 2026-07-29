const log = document.getElementById("log");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const threadIdDisplay = document.getElementById("threadIdDisplay");
const newThreadBtn = document.getElementById("newThreadBtn");

const THREAD_ID_KEY = "dev-retro-agent:thread-id";
const EMPTY_STATE_HTML = `
  POST /api/agent 로 메시지를 보내고 응답을 확인하는 테스트용 콘솔입니다.<br />
  아래 입력창에 메시지를 입력하고 Enter(Shift+Enter는 줄바꿈)를 누르세요.
`;

// crypto.randomUUID()는 HTTPS/localhost 같은 secure context에서만 존재한다.
// HTTP로만 서빙되는 배포 환경(EC2 등)에서도 동작하도록 폴백을 둔다.
function generateId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

let threadId = localStorage.getItem(THREAD_ID_KEY);
if (!threadId) {
  threadId = generateId();
  localStorage.setItem(THREAD_ID_KEY, threadId);
}

function renderThreadId() {
  threadIdDisplay.textContent = threadId.slice(0, 8);
  threadIdDisplay.title = threadId;
}
renderThreadId();

newThreadBtn.addEventListener("click", () => {
  threadId = generateId();
  localStorage.setItem(THREAD_ID_KEY, threadId);
  renderThreadId();
  log.innerHTML = `<div class="empty" id="emptyState">${EMPTY_STATE_HTML}</div>`;
});

function appendMessage(role, text) {
  document.getElementById("emptyState")?.remove();
  const div = document.createElement("div");
  div.className = "msg " + role;
  const roleLabel = document.createElement("span");
  roleLabel.className = "role";
  roleLabel.textContent = role === "user" ? "you" : role === "error" ? "error" : "agent";
  div.appendChild(roleLabel);

  const body = document.createElement("div");
  body.className = "body";
  if (role === "agent") {
    // agent 응답만 마크다운 -> HTML로 렌더링 (사용자 입력은 그대로 텍스트로 표시)
    body.innerHTML = DOMPurify.sanitize(marked.parse(text));
  } else {
    body.textContent = text;
  }
  div.appendChild(body);

  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

function appendThinking() {
  const div = document.createElement("div");
  div.className = "thinking";
  div.innerHTML = "<span></span><span></span><span></span>";
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  return div;
}

async function sendMessage(message) {
  const thinkingEl = appendThinking();
  sendBtn.disabled = true;
  try {
    const res = await fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        thread_id: threadId,
      }),
    });
    thinkingEl.remove();
    if (!res.ok) {
      const detail = await res.text();
      appendMessage("error", `[${res.status}] ${detail}`);
      return;
    }
    const data = await res.json();
    appendMessage("agent", data.message ?? "(빈 응답)");
  } catch (err) {
    thinkingEl.remove();
    appendMessage("error", String(err));
  } finally {
    sendBtn.disabled = false;
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  appendMessage("user", text);
  input.value = "";
  input.style.height = "44px";
  sendMessage(text);
});

// 한글 등 IME 조합을 확정하는 Enter는 전송으로 취급하지 않는다.
// (isComposing/keyCode 229는 그 keydown이 조합 확정용인지 알려주는 표준 신호)
let composing = false;
input.addEventListener("compositionstart", () => {
  composing = true;
});
input.addEventListener("compositionend", () => {
  composing = false;
});

input.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || e.shiftKey) return;
  if (composing || e.keyCode === 229) return;
  e.preventDefault();
  form.requestSubmit();
});

input.addEventListener("input", () => {
  input.style.height = "44px";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
});
