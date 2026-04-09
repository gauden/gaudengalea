import { getCollection, getEntry } from "astro:content";

type DatedEntry = Awaited<ReturnType<typeof getPublishedBlogEntries>>[number];

function byNewest<T extends { data: { pub_date: Date } }>(left: T, right: T): number {
  return right.data.pub_date.getTime() - left.data.pub_date.getTime();
}

function bySeriesOrder<T extends { data: { order?: number; pub_date: Date } }>(left: T, right: T): number {
  const leftOrder = left.data.order ?? Number.MAX_SAFE_INTEGER;
  const rightOrder = right.data.order ?? Number.MAX_SAFE_INTEGER;
  if (leftOrder !== rightOrder) {
    return leftOrder - rightOrder;
  }
  return left.data.pub_date.getTime() - right.data.pub_date.getTime();
}

export async function getPage(id: string) {
  const entry = await getEntry("pages", id);
  if (!entry) {
    throw new Error(`Missing page content: ${id}`);
  }
  return entry;
}

export async function getPublishedBlogEntries() {
  const entries = await getCollection("blog", ({ data }) => !data.draft);
  return entries.sort(byNewest);
}

export async function getPublishedLabEntries() {
  const entries = await getCollection("lab", ({ data }) => !data.draft);
  return entries.sort(byNewest);
}

export async function getPublishedPublications() {
  const entries = await getCollection("pub", ({ data }) => !data.draft);
  return entries.sort(byNewest);
}

export async function getTopLevelBlogEntries() {
  const entries = await getPublishedBlogEntries();
  return entries.filter((entry) => !entry.id.includes("/"));
}

export async function getTopLevelLabEntries() {
  const entries = await getPublishedLabEntries();
  return entries.filter((entry) => !entry.id.includes("/"));
}

export function getParentSlug(id: string): string | null {
  const lastSlash = id.lastIndexOf("/");
  return lastSlash === -1 ? null : id.slice(0, lastSlash);
}

export function getDirectChildren<T extends DatedEntry>(entries: T[], parentId: string): T[] {
  return entries
    .filter((entry) => getParentSlug(entry.id) === parentId)
    .sort(bySeriesOrder);
}

export async function getRecentHomeItems(limit = 8) {
  const [blog, lab, pubEntries] = await Promise.all([
    getPublishedBlogEntries(),
    getPublishedLabEntries(),
    getPublishedPublications(),
  ]);

  return [
    ...blog.map((entry) => ({ ...entry, section: "Blog" })),
    ...lab.map((entry) => ({ ...entry, section: "Lab" })),
    ...pubEntries.map((entry) => ({ ...entry, section: "Pub" })),
  ]
    .sort(byNewest)
    .slice(0, limit);
}

export async function getFeedItems(limit = 20) {
  const [blog, lab, pubEntries] = await Promise.all([
    getPublishedBlogEntries(),
    getPublishedLabEntries(),
    getPublishedPublications(),
  ]);

  return [...blog, ...lab, ...pubEntries].sort(byNewest).slice(0, limit);
}
