# Bike Science Pro · public beta

A browser-based cycling ride briefing: **How hard is this ride? How should I prepare? Which changes matter most?**

Try the fictional Sunday Loop immediately, or import a GPX locally. Estimate moving time, examine the elevation profile and demanding sections, check virtual cadence, and compare power, system mass, aerodynamic drag and rolling resistance independently.

## Languages

English and Czech are available from the header language selector. [Review in Czech](https://bike-science-pro-preview.roman-christov.workers.dev/?lang=cs) or [English](https://bike-science-pro-preview.roman-christov.workers.dev/?lang=en). Explicit links override the saved choice; otherwise the app uses the saved language, then the browser’s primary language (Czech or English fallback).

Switching languages keeps the imported GPX, inputs and calculated results. It also updates errors, route-quality warnings, chart accessibility text and downloaded briefings. Decimal input accepts either comma or point; displayed numbers follow the selected language. Only the language preference is stored locally. See [localization maintenance and review](docs/LOCALIZATION.md).

## Local setup

Use Node **20.19+ or 22.12+** and pnpm **11.25** (the checked-in `pnpm-lock.yaml` is the reproducible dependency lock).

```sh
corepack enable
corepack prepare pnpm@11.25.0 --activate
pnpm install --frozen-lockfile
pnpm dev
```

Open the local URL printed by Vite, normally `http://127.0.0.1:5173`. No Python or server-side computation is needed. Do not run the historical Streamlit app to review the beta.

```sh
pnpm check                    # numerical/GPX tests, TypeScript, production build
pnpm exec playwright install chromium
pnpm test:e2e                 # actual production build, desktop/mobile Chrome
pnpm preview                  # serve dist locally
```

Run `pnpm build` before `test:e2e` after changing source. Browser checks use port 4173. `BETA_URL` can point them at a separate preview URL. If Corepack is unavailable, install pnpm using its official installation instructions; some Node distributions no longer include Corepack.

## Architecture & privacy

- React/Vite frontend. Pure TypeScript domain modules in `src/model/` are independent of React.
- Parsing, elevation processing, simulation and comparisons run in a dedicated browser worker. Superseded jobs are terminated when inputs change.
- GPX XML is read into memory, never uploaded or stored persistently. No analytics, accounts, cookies, external fonts, maps or weather requests.
- `public/` contains only the icon and security headers. The demo is generated from a fictional elevation profile in code; `sample_routes/my_ride.gpx` is **not** imported, copied to `dist`, or published.
- Save briefing downloads a local text file with route name and chosen settings, not GPS coordinates. Refresh/clear resets imported data. Cloudflare still handles ordinary static-asset traffic and may retain infrastructure request logs.
- No backend, database, API keys, or remote route processing. Production CSP blocks outbound connections from the app.

## Model

See [MODEL.md](docs/MODEL.md) for equations, sources, approximations, solver behavior, GPX handling and intentional differences from the prototype. Numerical checks verify the implementation, not outdoor finish-time accuracy. The beta has no empirical route-time validation or confidence interval.

Sustainable power is absolute crank power, not automatically derived from FTP or rider weight. A lower weight comparison keeps watts fixed. Constant pedaling, optional coasting below −3%, and a user-selected speed ceiling are explicit assumptions. Gearing affects reported cadence only. Energy expenditure is an illustrative efficiency range, **not** an intake recommendation.

## Cloudflare

[Open the deployed review preview](https://bike-science-pro-preview.roman-christov.workers.dev). Updated 16 October 2026 with Czech localization; all 22 hosted desktop/mobile browser checks pass. Production-domain publication remains for owner review.

[Deployment instructions](docs/DEPLOYMENT.md) cover an isolated `bike-science-pro-preview` Worker, the production Worker, verification and rollback. Workers static assets serve `dist`; no custom domain is configured. The Spořilov repository and deployment were left untouched. Its existing project uses Pages; this project uses Workers static assets as explicitly requested.

```sh
pnpm exec wrangler login
pnpm deploy:preview
```

Authenticate to the intended Cloudflare account first. Review the returned `workers.dev` preview before production-domain publication. This work did not publish a production domain or create an unauthenticated temporary Cloudflare account.

## Deferred for a credible first release

Accounts, cloud route storage, live weather, Strava, payments and AI assistant are deferred. Distance/ascent-only manual routes are excluded because they cannot define terrain distribution. Unsupported sweat, sodium, carbohydrate and recovery recommendations were removed from the beta. Target-time estimates remain a bounded numerical utility with tests, not a public promise of physiological feasibility.

## Historical Python prototype

The original `.py` modules, `tests/`, route file and original [README](docs/LEGACY_README.md) are retained for history and reference. They are **not** the beta runtime, and their known solver, segmentation and biology issues are not certified by the new tests. Historical setup: `pip install -r requirements.txt pytest`, then `python -m pytest tests` or `streamlit run streamlit_app.py`.

[Implementation plan and baseline](docs/IMPLEMENTATION_PLAN.md) · [Verification and launch notes](docs/VERIFICATION.md) · [PR review findings](docs/PR_REVIEW.md)
