## Gauden Galea

### Personal website

[http://www.gaudengalea.com](http://www.gaudengalea.com)

## Local development on `ulysses`

Install dependencies:

```bash
npm ci
```

Run the local Astro dev server:

```bash
npm run dev
```

Build the static site:

```bash
npm run build
```

Hosted content editing uses Pages CMS with `.pages.yml` in the repo root. No CMS service is deployed on `molly`; the editor runs against GitHub and the resulting commits are deployed by the same GitHub Actions workflow.

Run the migration utility tests:

```bash
uv run pytest
```
