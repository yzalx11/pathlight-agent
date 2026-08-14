const MAX_VISIBLE_TEXT_LENGTH = 30000;

function collectVisibleJobPage() {
  const visibleText = (document.body?.innerText || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join("\n")
    .slice(0, MAX_VISIBLE_TEXT_LENGTH);

  return {
    page_title: document.title.trim() || "BOSS 职位页面",
    source_link: window.location.href,
    visible_text: visibleText,
  };
}

chrome.runtime.onMessage.addListener((message, _, sendResponse) => {
  if (message?.type !== "pathlight:read-visible-job") return;
  sendResponse(collectVisibleJobPage());
});
