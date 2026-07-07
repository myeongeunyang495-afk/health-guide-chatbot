const documents = {
  "본사": "1. 본사_2026년 건강진단 직원 안내자료(4개병원).hwp",
  "서울본부": "2. 서울본부_2026년 건강진단 직원 안내자료(6개병원).hwp",
  "수도권동부본부": "3. 수도권동부본부_2026년건강진단 직원 안내자료(13개병원).hwp",
  "수도권서부본부": "4. 수도권서부본부_2026년 건강진단 직원 안내자료(8개병원).hwp",
  "강원본부": "5. 강원본부_2026년 건강진단 직원 안내자료(8개병원).hwp",
  "대전충남본부": "6. 대전충남본부_2026년 건강진단 직원 안내자료(8개병원).hwp",
  "충북본부": "7. 충북본부_2026년 건강진단 직원 안내자료(7개병원).hwp",
  "전북본부": "8. 전북본부_2026년 건강진단 직원 안내자료(7개병원).hwp",
  "광주본부": "9. 광주본부_2026년 건강진단 직원 안내자료(10개병원).hwp",
  "전남본부": "10. 전남본부_2026년 건강진단 직원 안내자료(8개병원).hwp",
  "대구본부": "11. 대구본부_2026년 건강진단 직원 안내자료(8개병원).hwp",
  "경북본부": "12. 경북본부_2026년 건강진단 직원 안내자료(7개 병원).hwp",
  "부산경남본부": "13. 부산경남본부_2026년 건강진단 직원 안내자료(11개병원).hwp",
  "철도교통관제센터": "14. 철도교통관제센터_2026년 건강진단 직원 안내자료(2개병원).hwp",
  "수도권철도차량정비단": "15. 수도권철도차량정비단_2026년 건강진단 직원 안내자료(2개병원).hwp",
  "대전철도차량정비단": "16. 대전철도차량정비단_2026년 건강진단 직원 안내자료(1개병원).hwp",
  "부산철도차량정비단": "17. 부산철도차량정비단_2026년 건강진단 직원 안내자료(3개병원).hwp",
  "시흥철도차량정비단": "18. 시흥철도차량정비단_2026년 건강진단 직원 안내자료(2개병원).hwp",
  "고속시설사업단": "19. 고속시설사업단_2026년 건강진단 직원 안내자료(3개병원).hwp",
  "고속전기사업단": "20. 고속전기사업단_2026년 건강진단 직원 안내자료(2개병원).hwp",
};

const organizations = Object.keys(documents);

const pdfPreviewOrganizations = new Set([
  "본사",
  "서울본부",
  "수도권동부본부",
  "수도권서부본부",
  "강원본부",
  "대전충남본부",
  "충북본부",
  "전북본부",
  "광주본부",
]);

const previewPageCounts = {
  "본사": 12,
  "서울본부": 15,
  "수도권동부본부": 34,
  "수도권서부본부": 20,
  "강원본부": 27,
  "대전충남본부": 20,
  "충북본부": 17,
  "전북본부": 14,
  "광주본부": 21,
};

const specialHazards = Object.fromEntries(
  organizations.map((org) => [org, []]),
);

const modeConfig = {
  guide: {
    label: "소속기관",
    title: "소속기관 검진 안내자료 조회",
    help: "선택한 소속기관의 건강진단 안내자료가 아래에 자동으로 표시됩니다.",
    noteVisible: true,
  },
  special: {
    label: "대상소속",
    title: "특수검진 대상소속 조회",
    help: "선택한 대상소속의 특수검진 유해인자가 아래에 표시됩니다.",
    noteVisible: false,
  },
};

const quickQuestions = [
  "소속기관 검진 안내자료 조회",
  "특수검진 대상소속 조회",
  "건강검진은 어디서 받을 수 있나요?",
  "유해인자는 언제 볼 수 있나요?",
];

const organizationSelect = document.querySelector("#organizationSelect");
const organizationLabel = document.querySelector("#organizationLabel");
const organizationTitle = document.querySelector("#organizationTitle");
const selectionHelp = document.querySelector("#selectionHelp");
const modeNote = document.querySelector("#modeNote");
const modeButtons = document.querySelectorAll(".mode-toggle button");
const materialEyebrow = document.querySelector("#materialEyebrow");
const materialTitle = document.querySelector("#materialTitle");
const downloadLink = document.querySelector("#downloadLink");
const documentViewer = document.querySelector("#documentViewer");
const viewerFallback = document.querySelector("#viewerFallback");
const quickQuestionsNode = document.querySelector("#quickQuestions");
const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const chatInput = document.querySelector("#chatInput");
const resetChat = document.querySelector("#resetChat");
const chatTrigger = document.querySelector("#chatTrigger");
const chatModal = document.querySelector("#chatModal");
const closeChat = document.querySelector("#closeChat");

let currentMode = "guide";

function option(label, value = label) {
  const node = document.createElement("option");
  node.value = value;
  node.textContent = label;
  return node;
}

function selectedOrganization() {
  return organizationSelect.value;
}

function pdfUrl(org) {
  return `pdfs/${documents[org].replace(/\.hwp$/i, ".pdf")}`;
}

function hasPdfPreview(org) {
  return pdfPreviewOrganizations.has(org);
}

function imagePreviewBase(org) {
  return `preview-images/${documents[org].replace(/\.hwp$/i, "")}`;
}

function renderImagePreview(org) {
  const count = previewPageCounts[org] || 0;
  if (!count) {
    documentViewer.replaceChildren();
    return;
  }

  const base = imagePreviewBase(org);
  const pages = [];
  for (let index = 1; index <= count; index += 1) {
    const page = String(index).padStart(3, "0");
    const figure = document.createElement("figure");
    figure.className = "preview-page";

    const img = document.createElement("img");
    img.src = encodeURI(`${base}/page-${page}.png`);
    img.alt = `${org} 안내자료 ${index}페이지`;
    img.loading = index <= 2 ? "eager" : "lazy";

    const caption = document.createElement("figcaption");
    caption.textContent = `${index} / ${count}`;

    figure.append(img, caption);
    pages.push(figure);
  }
  documentViewer.replaceChildren(...pages);
}

function renderHazards(org) {
  const hazards = specialHazards[org] || [];
  const wrapper = document.createElement("div");
  wrapper.className = "hazard-preview";

  if (!hazards.length) {
    wrapper.innerHTML = `
      <div class="empty-state">
        <strong>${org} 특수검진 유해인자 자료 등록 전</strong>
        <p>유해인자 원자료를 연결하면 이 영역에 대상 유해인자, 대상 직무, 검진 주기가 자동으로 표시됩니다.</p>
      </div>
    `;
    documentViewer.replaceChildren(wrapper);
    return;
  }

  wrapper.replaceChildren(
    ...hazards.map((item) => {
      const card = document.createElement("article");
      card.className = "hazard-card";
      card.innerHTML = `
        <strong>${item.name}</strong>
        <p>${item.detail}</p>
      `;
      return card;
    }),
  );
  documentViewer.replaceChildren(wrapper);
}

function renderOrganizations() {
  organizationSelect.replaceChildren(...organizations.map((org) => option(org)));
  renderMode();
}

function setMode(mode) {
  currentMode = mode;
  modeButtons.forEach((button) => {
    const active = button.dataset.mode === mode;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  renderMode();
  organizationSelect.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderMaterialPanel() {
  const org = selectedOrganization();

  if (currentMode === "guide") {
    const canPreviewPdf = hasPdfPreview(org);
    materialEyebrow.textContent = "건강진단 안내자료";
    materialTitle.textContent = `${org} 2026년 건강진단 직원 안내자료`;
    downloadLink.href = encodeURI(pdfUrl(org));
    downloadLink.download = documents[org].replace(/\.hwp$/i, ".pdf");
    downloadLink.hidden = !canPreviewPdf;

    if (canPreviewPdf) {
      renderImagePreview(org);
    } else {
      documentViewer.replaceChildren();
    }

    viewerFallback.innerHTML = `
      <strong>검진 안내자료</strong>
      <p>${canPreviewPdf ? "선택한 소속기관의 안내자료가 이미지로 표시됩니다. PDF 다운로드도 가능합니다." : "아직 이 소속기관의 PDF 파일이 없습니다. PDF가 추가되면 미리보기와 다운로드가 가능합니다."}</p>
    `;
    return;
  }

  materialEyebrow.textContent = "특수검진 유해인자";
  materialTitle.textContent = `${org} 특수검진 유해인자`;
  downloadLink.hidden = true;
  renderHazards(org);
  viewerFallback.innerHTML = `
    <strong>특수검진 대상소속 조회</strong>
    <p>${org}의 특수검진 유해인자 확인 영역입니다.</p>
  `;
}

function renderMode() {
  const config = modeConfig[currentMode];
  organizationLabel.textContent = config.label;
  organizationTitle.textContent = config.title;
  selectionHelp.textContent = `${config.help} 현재 선택: ${selectedOrganization()}`;
  modeNote.classList.toggle("hidden", !config.noteVisible);
  renderMaterialPanel();
}

function addMessage(text, sender = "bot") {
  const node = document.createElement("div");
  node.className = `message ${sender}`;
  node.textContent = text;
  chatLog.append(node);
  chatLog.scrollTop = chatLog.scrollHeight;
  return node;
}

function answerQuestion(rawQuestion) {
  const question = rawQuestion.replace(/\s/g, "").toLowerCase();
  const org = selectedOrganization();

  if (question.includes("특수") || question.includes("유해")) {
    return `특수검진 대상소속 조회를 선택한 뒤 대상소속을 고르면 ${org}의 유해인자 확인 영역이 표시됩니다.`;
  }

  if (question.includes("어디") || question.includes("전국") || question.includes("건강검진")) {
    return "본인 소속과 관계없이 전국 어디서나 건강검진이 가능합니다.\n소속기관 검진 안내자료 조회에서 기관을 선택하면 안내자료를 미리보고 PDF로 다운로드할 수 있습니다.";
  }

  if (question.includes("안내") || question.includes("자료") || question.includes("소속")) {
    return `현재 선택된 소속기관은 ${org}입니다.\n아래 안내자료 영역에서 미리보기와 PDF 다운로드를 확인할 수 있습니다.`;
  }

  return "먼저 조회 유형을 선택하고, 아래에서 소속기관 또는 대상소속을 선택해 주세요.";
}

function openChat() {
  chatModal.classList.remove("hidden");
  chatInput.focus();
}

function closeChatModal() {
  chatModal.classList.add("hidden");
  chatTrigger.focus();
}

function askQuestion(question) {
  openChat();
  addMessage(question, "user");
  addMessage(answerQuestion(question));
}

modeButtons.forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
organizationSelect.addEventListener("change", renderMode);
chatTrigger.addEventListener("click", openChat);
closeChat.addEventListener("click", closeChatModal);

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = chatInput.value.trim();
  if (!question) return;
  chatInput.value = "";
  askQuestion(question);
});

resetChat.addEventListener("click", () => {
  chatLog.replaceChildren();
  addMessage("안녕하세요. 검진 안내자료 조회 또는 특수검진 대상소속 조회에 대해 물어보세요.");
});

quickQuestionsNode.replaceChildren(
  ...quickQuestions.map((question) => {
    const node = document.createElement("button");
    node.type = "button";
    node.textContent = question;
    node.addEventListener("click", () => askQuestion(question));
    return node;
  }),
);

renderOrganizations();
resetChat.click();
