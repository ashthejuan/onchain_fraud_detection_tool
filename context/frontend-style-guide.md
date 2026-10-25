# Frontend Style Guide

**Purpose:** Visual direction for the On-Chain Fraud Detection & AI Investigation Platform frontend (Phase 4).  
**Reference:** [Inferact](https://inferact.ai/), reviewed 25 October 2026.  
**Status:** Implementation guide; adapt the reference’s design philosophy to an investigative dashboard rather than reproduce its marketing site.

## Design idea

Treat the interface like a **forensic instrument panel**: calm, exact, and built around evidence. Inferact pairs confident editorial typography and generous space with technical diagrams, strong blue fields, and a restrained yellow signal. Carry that sense of control and engineered precision into an analyst workspace. The dashboard should feel dependable and legible before it feels futuristic.

The reference is a marketing site, while this product is a dense working application. Borrow its visual character—clear hierarchy, purposeful color, technical imagery, and confident simplicity—while keeping application conventions that aid scanning: persistent navigation, compact tables, filters, and explicit state labels.

## Visual principles

1. **Evidence leads.** Make the transaction, risk score, severity, rule triggers, and supporting observations the most legible content. AI interpretation is visibly secondary and separately labeled.
2. **Structure over decoration.** Use strong type scale, aligned columns, restrained rules, and purposeful whitespace. Do not add panels, icons, charts, or labels that do not help an analyst decide what to inspect.
3. **Precision with a human voice.** Use concise, plain-language labels and explanations. Preserve exact identifiers and amounts; provide copy affordances for long hashes and addresses.
4. **Color carries meaning.** Use the brand blue to identify key data and the primary action. Reserve amber for attention or investigation cues. Risk states use a consistent severity system, always paired with text and never communicated by color alone.
5. **Show the system honestly.** Distinguish observed facts from model-generated interpretation. Show units, time context, provenance, loading, empty, stale, and error states without inventing data.

## Palette

Start with these implementation tokens and tune only after seeing them in the real UI. The reference’s blue and yellow are translated rather than copied literally.

| Token | Value | Use |
|---|---|---|
| `canvas` | `#F4F6F8` | Main application background |
| `surface` | `#FFFFFF` | Tables, forms, and focused content surfaces |
| `surface-muted` | `#E9EEF3` | Selected rows, quiet inset regions |
| `ink` | `#15212C` | Primary text and strong neutral controls |
| `ink-muted` | `#536372` | Secondary text; retain readable contrast |
| `line` | `#D5DEE6` | Dividers, table rules, and control borders |
| `blue` | `#1769AA` | Primary action, links, and the main data series |
| `blue-soft` | `#E5F1FA` | Selected or informational state backgrounds |
| `amber` | `#D59A24` | Attention marker and limited highlight; do not use as body text on white |
| `success` | `#26734D` | Resolved/healthy state |
| `warning` | `#99620A` | Medium risk and pending review |
| `danger` | `#B53C37` | High/critical risk and failed state |

Severity mapping follows the backend: **Low** uses neutral/green, **Medium** amber, **High** red, **Critical** deep red plus a clear text label. Scores remain numeric. Use pale state backgrounds with dark foreground text. Avoid large saturated fills, gradients, glows, and using blue or amber as general decoration.

## Typography

- Use one readable sans-serif family for interface text and figures. Prefer a project-bundled or system-available face; do not make a network font a runtime dependency.
- Use tabular numerals for scores, amounts, counts, and timestamps. Use monospace only for hashes, addresses, and code-like identifiers.
- Establish a compact, stable scale: page title 24–28 px; section title 16–18 px; body and controls 14–16 px; metadata 12–13 px. Do not shrink essential evidence below 12 px.
- Use medium weight and ink color for titles. Use sentence case for headings and table labels. Avoid decorative all-caps tracking.
- Keep line length comfortable for report prose. Technical identifiers may wrap or truncate visually only when the full value remains available by copy, expansion, or tooltip.

## Layout and surfaces

- Use a persistent left navigation on desktop with product name/mark and the core destinations: Overview, Transactions, Alerts. Keep the active item quiet and unmistakable through a neutral surface or text-weight change.
- Give pages consistent outer margins and a clear title/action row. Put the screen’s most useful finding near the top; avoid a large empty hero area.
- Build with a 12-column responsive grid where useful. Align page titles, filters, table edges, and section headings to shared grid lines.
- Prefer a flat canvas and white work surfaces. Separate regions with whitespace and a 1 px border or a small tone shift; do not combine heavy borders with shadows. Reserve shadows for overlays.
- Use a consistent compact radius (4–6 px) for controls and panels. Keep table rows dense but comfortably selectable; do not zebra-stripe.
- At narrow widths, collapse navigation into a labeled menu, turn tables into two-line records or contained horizontal scroll, and keep key actions and risk status visible.

## Components and data display

### Overview

- Lead with a useful operational summary, not a greeting. Counts should be derived from the displayed/API data and include their time window where relevant.
- Show severity breakdown as labeled values or a restrained single-hue chart. Charts must explain an actual question; omit them when a few counts are clearer.
- Give the recent critical/high alert list enough room to show real transaction identifiers, score, severity, and time.

### Tables and filters

- Use sentence-case, muted column headers; thin row separators; no decorative header band or alternating rows.
- Right-align numeric values and use tabular figures. Include units and consistent precision for amounts and scores.
- Keep hash/address typography monospace and truncate in the middle when possible; expose the full string on selection or copy.
- Put filters near the list they affect. Make active filters visible and removable. Search should state what fields it searches.
- Keep status and severity readable as text. Small tinted labels are acceptable inside rows, not as oversized pills above page headings.

### Risk and evidence

- Display score, severity, and review status as separate concepts.
- For each triggered rule, show its plain-language name and the specific observation/value that caused it to trigger.
- Use amber sparingly for investigation attention; reserve red for high/critical risk or errors. Always pair color with label, icon/shape only when useful, or text.
- Repeat the persistent disclaimer: “Risk indicators do not prove fraud.” Place it where it remains available without dominating the evidence.

### Investigation reports

- Label generated content **AI-generated investigative aid**.
- Keep **Observed evidence**, **Interpretation**, **Recommended checks**, and **Limitations** visually distinct and in that order.
- Evidence references should link back to the corresponding transaction, rule, or wallet record when supported.
- Present pending, failed, and retry states inline in the report area with sanitized explanations.

### Wallets and identifiers

- Treat wallet addresses and transaction hashes as identifiers, not prose: monospace, copyable, and consistently shortened in tables.
- Present local flag provenance as a recorded fact with its source/status. Do not imply identity attribution or external intelligence.

## Interaction and states

- Primary buttons use a solid blue fill with white text; secondary actions are quiet outlined or text controls. Keep one obvious primary action per region.
- Use visible keyboard focus, clear hover feedback, and at least 40 px control hit areas where practical.
- Loading preserves the final layout and uses static placeholders; avoid shimmer gradients. Empty states explain what is absent and offer the next relevant action. Errors stay within the failed region and offer retry when possible.
- Confirm destructive or consequential changes. Review status changes should show the saved value and remain filterable.
- Respect reduced-motion settings. Use short transitions only to clarify state changes; no ambient movement or parallax in the analyst workspace.

## Avoid

- Copying Inferact’s logo, illustrations, wording, or bespoke site layouts.
- Generic “AI dashboard” decoration: gradient backgrounds, glass panels, neon glows, KPI icon tiles, arbitrary sparklines, rainbow charts, and decorative blockchain node patterns.
- Calling a flagged transaction “fraudulent” or presenting model interpretation as verified fact.
- Fake or inflated metrics, unlabeled units, unexplained scores, or alerts shown without their evidence.

## Source interpretation

Inferact’s public site communicates engineering control through large clear headings, substantial blue imagery, yellow callouts, and diagrams tied to concrete system capabilities. This guide translates those signals into a restrained analyst application: blue anchors important data and actions; amber highlights attention; diagrammatic visuals are used only when they explain transaction or system evidence. The application’s PRD and Phase 4 requirements take precedence for information architecture and behavior.
