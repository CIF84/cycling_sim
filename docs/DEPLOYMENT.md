# Cloudflare deployment

Bike Science Pro is an independent Workers static-assets app, configured in `wrangler.jsonc`. The browser does all simulation/GPX work. No backend script, routes, custom domain, database, secrets, or paid bindings are configured.

Spořilov 3D lives in a separate repository and currently uses Cloudflare Pages. Its files and hosting settings were read only to establish the existing approach; they were not modified. Bike Science Pro intentionally follows the requested Workers static-assets deployment rather than reusing the Spořilov Pages project.

## Deploy a separate review preview

From this repository with Node and pnpm installed:

```sh
pnpm install --frozen-lockfile
pnpm check
pnpm exec playwright install chromium
pnpm test:e2e
pnpm exec wrangler login
pnpm exec wrangler whoami
pnpm deploy:preview
```

Complete Cloudflare OAuth yourself and verify that `whoami` identifies the intended account. If the account has multiple account IDs, supply the correct `CLOUDFLARE_ACCOUNT_ID` in the environment or add that ID to the local configuration. Do not borrow Spořilov credentials/configuration or place tokens in source files.

The preview command deploys **bike-science-pro-preview**, a separate worker, and returns its `https://bike-science-pro-preview.<account-subdomain>.workers.dev` URL. That is a shareable public beta preview, not a custom-domain production release. Inspect the actual returned URL, not the placeholder above. `preview_urls` are disabled; the preview uses its own isolated worker and deployment history.

On 14 October 2026, the owner completed Cloudflare OAuth and the separate preview was deployed. It was updated on 15 October with the PR review fixes and on 16 October with English/Czech localization and groupset presets:

- Preview: [Bike Science Pro](https://bike-science-pro-preview.roman-christov.workers.dev)
- Czech review link: [Čeština](https://bike-science-pro-preview.roman-christov.workers.dev/?lang=cs)
- Worker: `bike-science-pro-preview`
- Version: `4e381995-5515-4717-824a-6d9a2c9d9b8f` (25 manufacturer-sourced groupset presets)
- The groupset release passed all 102 unit checks, strict TypeScript, the production build and all 26 hosted desktop/mobile browser checks. Security headers and all five public asset hashes were verified. Preset/manual editing, source links, unchanged ride estimates, Czech/English switching and 320 px overflow are covered.

The first immediate test run encountered transient Cloudflare 404 responses for the new Worker and assets. A complete rerun after propagation passed without retries or application changes. Allow the initial deployment to propagate before sharing its URL. Those preview releases did not publish production; the owner-approved production launch is recorded below. No temporary account was created.

## Review the hosted preview

```sh
BETA_URL='https://bike-science-pro-preview.roman-christov.workers.dev' pnpm test:e2e
```

The tests should allow that origin in their outbound-request assertion (the test already derives the page origin dynamically). Use the returned real URL. Check demo, changed watts/wind, GPX with and without elevations, quality notes, profile slider, groupset selection, manual chainring/cassette editing, reset and downloaded briefing. Inspect at desktop and phone widths. Switch English/Čeština with a GPX loaded, enter decimal commas, check translated warnings and download the Czech briefing. Only the language preference should survive a refresh. Confirm network traffic contains only static-asset requests, with no GPX uploads or external fonts/analytics. Browser-specific download handling may differ on phones.

Keep the local model limitations visible. For a broad launch, calibrate a few representative outdoor rides with known power, route elevation and conditions; beta estimates are not finish-time promises.

## Production public beta

The owner approved publication on **16 October 2026**. [PR #1](https://github.com/CIF84/cycling_sim/pull/1) was merged into `main` as `d01d1470fb4765979a3fd0bb81cf7cb72b40a3ad`, preserving the reviewed beta commits. The verified build from that revision was published to the top-level production Worker with `pnpm exec wrangler deploy --env ''`.

- Production: [Bike Science Pro](https://bike-science-pro.roman-christov.workers.dev) · [Čeština](https://bike-science-pro.roman-christov.workers.dev/?lang=cs) · [English](https://bike-science-pro.roman-christov.workers.dev/?lang=en)
- Worker: `bike-science-pro`
- Version: `64b18568-b3d0-47a0-a292-4c5ed8bedfe1`
- Verification: 102 unit checks, strict TypeScript and production build pass; all 26 production desktop/mobile browser checks pass without retries. HTTPS/security headers and all five public asset bytes match the verified build.
- The preview Worker remains separate and unchanged. No custom domain or Spořilov resource was configured or changed.

For subsequent approved releases, use the intended `main` revision, run the checks above, then:

```sh
pnpm deploy:production
```

This deploys **bike-science-pro** to its own `workers.dev` address. No custom domain has been selected. A future custom domain requires the owner to identify it; then configure that domain for this Worker through Cloudflare’s dashboard or explicit routes configuration. Confirm account and zone before adding it. Do not attach the Spořilov domain or alter its deployment.

Verify each production release with:

```sh
BETA_URL='https://bike-science-pro.roman-christov.workers.dev' pnpm test:e2e
```

`BETA_URL` is the test suite's target URL setting; it also supports the production address.

For Git-connected Workers Builds later, use this repo root, Node 22+, install `pnpm install --frozen-lockfile`, build `pnpm build`, and deploy `pnpm exec wrangler deploy --env ''` (or `--env preview` for the separate preview). Keep the public static files limited to `dist`. Production source is on `main`; the original beta review is retained in PR #1 and the `codex/bike-science-pro-beta` branch. This implementation does not configure Git-connected deployment, CI, or custom-domain publication. Deployments remain explicit commands after review; pushing a documentation commit does not redeploy the app.

## Local Workers verification

```sh
pnpm build
pnpm exec wrangler deploy --env preview --dry-run
pnpm exec wrangler dev --env preview --port 8787 --local
# In a second terminal:
BETA_URL=http://127.0.0.1:8787 pnpm test:e2e
```

Compatibility date `2026-10-13` matches the installed pinned workerd runtime; choosing the next day failed locally and was corrected. Dependency versions are locked, and `pnpm-workspace.yaml` explicitly permits the esbuild/workerd installation scripts.

`public/_headers` is copied into `dist`: CSP permits same-origin scripts/workers and local inline styles but blocks outbound connections; no framing, camera, microphone or geolocation access. The Vite development server does not enforce these hosting headers; the Workers-local suite does.

## Rollback and removal

Redeploy a known-good checkout with the same preview or production command; alternatively use the worker’s deployment history in Cloudflare to roll back. Preview and production have separate histories. To retire a preview, disable its workers.dev route or delete **only bike-science-pro-preview** in the dashboard. Do not change Spořilov. Deletion is not part of this implementation.

Official references: [Workers static assets](https://developers.cloudflare.com/workers/static-assets/), [SPA routing](https://developers.cloudflare.com/workers/static-assets/routing/single-page-application/), [asset security headers](https://developers.cloudflare.com/workers/static-assets/headers/).
