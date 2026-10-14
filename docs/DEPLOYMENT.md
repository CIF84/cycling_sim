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

On 14 October 2026, the owner completed Cloudflare OAuth and the separate preview was deployed successfully:

- Preview: [Bike Science Pro](https://bike-science-pro-preview.roman-christov.workers.dev)
- Worker: `bike-science-pro-preview`
- Version: `742d3032-d6eb-40f7-968e-1b436ce5af97`
- All 8 hosted desktop/mobile browser checks passed. HTTPS returned 200 with the configured security headers, and all 5 public assets matched the local production build byte for byte.

The first immediate test run encountered transient Cloudflare 404 responses for the new Worker and assets. A complete rerun after propagation passed without retries or application changes. Allow the initial deployment to propagate before sharing its URL. No production Worker or custom domain was deployed or changed, and no temporary account was created.

## Review the hosted preview

```sh
BETA_URL='https://bike-science-pro-preview.roman-christov.workers.dev' pnpm test:e2e
```

The tests should allow that origin in their outbound-request assertion (the test already derives the page origin dynamically). Use the returned real URL. Check demo, changed watts/wind, GPX with and without elevations, quality notes, profile slider, cassette editing, reset and downloaded briefing. Inspect at desktop and phone widths. Confirm network traffic contains only static-asset requests, with no GPX uploads or external fonts/analytics. Browser-specific download handling may differ on phones.

Keep the local model limitations visible. For a broad launch, calibrate a few representative outdoor rides with known power, route elevation and conditions; beta estimates are not finish-time promises.

## Production after owner review

```sh
pnpm deploy:production
```

This deploys **bike-science-pro**, currently to its own `workers.dev` address only. Publication to a production custom domain is intentionally left for owner review. After that review, add a Workers custom domain through Cloudflare’s dashboard or explicit routes configuration for this worker. Confirm account and zone before adding it. Do not attach the Spořilov domain or alter its deployment.

For Git-connected Workers Builds later, use this repo root, Node 22+, install `pnpm install --frozen-lockfile`, build `pnpm build`, and deploy `pnpm exec wrangler deploy` (or `--env preview` for the separate preview). Keep the public static files limited to `dist`. Source review uses the `codex/bike-science-pro-beta` branch. This implementation does not configure Git-connected deployment, CI, or custom-domain publication; production deployment remains an explicit step after owner review.

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
