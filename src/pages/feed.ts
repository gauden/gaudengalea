import rss from "@astrojs/rss";
import { getFeedItems } from "../lib/content";
import { SITE, stripMarkup } from "../lib/site";

export async function GET(context) {
  const page = new URL("/feed", context.site);
  const items = await getFeedItems();

  return rss({
    title: "gaudengalea.com — All Updates",
    description: "Site-wide feed of recent updates",
    site: context.site,
    customData: `<link rel="self" href="${page.toString()}" />`,
    items: items.map((entry) => ({
      title: entry.data.title,
      pubDate: entry.data.pub_date,
      description: entry.data.summary || stripMarkup(entry.body).slice(0, 200),
      link: `/${entry.collection}/${entry.id}/`,
      content: entry.body,
      author: SITE.author,
    })),
  });
}
