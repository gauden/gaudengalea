export const SITE = {
  title: "Gauden Galea",
  author: "Gauden Galea",
  email: "contact@gaudengalea.com",
  linkedin: "https://www.linkedin.com/in/gauden/",
  description:
    "A resume, sandbox, and hub connecting Gauden Galea's public health work with coding, digital health, AI, and other interests.",
};

export function pageTitle(title: string): string {
  return `${title} — ${SITE.author}`;
}

export function formatDate(value: Date): string {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(value);
}

export function stripMarkup(value: string): string {
  return value
    .replace(/<[^>]+>/g, " ")
    .replace(/\[[^\]]+\]\([^)]+\)/g, " ")
    .replace(/[#*_`>~-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function renderInlineMarkdown(value: string): string {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>");
}

export function makeExcerpt(summary: string | undefined, body: string, maxLength = 220): string {
  if (summary && summary.trim().length > 0) {
    return summary.trim();
  }

  const text = stripMarkup(body);
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength).trimEnd()}…`;
}
