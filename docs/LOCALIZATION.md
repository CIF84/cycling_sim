# Website localization

The public beta supports English (`en`) and Czech (`cs`, the language code; `CZ` is the country code). The brand, user-supplied GPX filenames, manufacturer names and academic source names stay unchanged. Repository setup/model documentation and linked research retain their original language; the complete in-app model explanation is translated.

## Review the Czech experience

Open [the Czech preview](https://bike-science-pro-preview.roman-christov.workers.dev/?lang=cs). Use the header selector to compare English and Czech without losing the current route, settings, profile position or calculation. The selected language also applies to saved text briefings.

Language selection order is the explicit `?lang=cs` or `?lang=en` link, the saved language, then the browser’s primary language. Czech browser settings choose Czech; unsupported languages fall back to English. Switching updates the URL without navigating. If local storage is blocked, the selector and explicit URL still work. The document language, page title and description update for accessibility and browser tools.

Only `bike-science-language` is saved in browser local storage. GPX data and ride settings remain in memory. The privacy disclosure states this. No translation service, extra network request, cookie or account is introduced.

Review terminology in particular: **udržitelný výkon** (sustainable power), **valivý odpor** (rolling resistance), **kadence** (cadence, displayed as ot/min), and **rychlostní limit modelu** (model speed ceiling, explicitly not a safe-speed recommendation). “Energetický výdej” remains separate from suggested food intake. Czech text preserves the English model’s limitations and uncertainty.

## Implementation

- `src/i18n/cs.ts`: typed Czech catalog keyed by English source messages. Use whole sentences and named placeholders for dynamic messages. Avoid building translated grammar from unrelated fragments. Numbered warning labels avoid ambiguous plural forms.
- `src/i18n/format.ts`: language selection, `Intl.NumberFormat`, template formatting and strict decimal parsing. Decimal comma and point are accepted; mixed separators, grouping, exponent notation and trailing text are rejected rather than partially parsed. GPX numeric parsing is unchanged and follows the GPX/XML representation.
- `src/i18n/context.tsx`: language state, selection persistence and React formatting helpers.
- `src/model/messages.ts`: serializable message keys and parameters, including nested field labels and decimal precision. Errors retain English `Error.message` for non-UI callers. The worker returns message data, never pretranslated strings. Switching language therefore does not restart the simulation or reload a route. Model code uses the catalog's key type only; the translation catalog is not bundled into the worker.
- Inputs preserve in-progress editing and the underlying number when switching language. Stable field IDs keep label associations intact. Positive-only fields use the decimal keyboard; signed fields retain a text keyboard so negative wind/altitude/temperature remain enterable on phones.
- Equations, physical constants, scenario changes and GPX processing behavior are unchanged by localization.

To add another language, provide a catalog satisfying `Record<MessageKey, string>`, extend the locale validation/selection and formatting map, and add its native name to the selector. Keep all placeholders, localize complete messages, and add browser coverage for that language. English source-key changes require updating translations and call sites; TypeScript catches unknown keys.

## Verification

- 22 localization unit cases cover selection precedence/fallback, comma and point parsing, rejected ambiguous values, locale formatting, all catalog placeholders, structured validation messages and comparison precision. All 49 existing numerical/GPX/profile checks also pass.
- Eight added browser checks (four scenarios at desktop and mobile sizes) cover Czech defaults, explicit/saved choices, blocked storage, language changes without new calculation workers, preserved inputs and GPX names, errors and warnings that switch live, decimal commas, chart controls, localized downloads, privacy and layout.
- Existing English browser checks remain in place. Czech and English advanced forms pass the automated Axe accessibility checks. Chromium is covered; actual iOS Safari/Android keyboards still need real-device review.
- The translation has been checked in context and is ready for the owner's native-language review. It has not had independent professional translation review.
