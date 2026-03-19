# DESIGN

## Benchmark
- Profile: Finahunt research cockpit
- Heading font: Space Grotesk
- Body font: IBM Plex Sans
- Background: #07111f
- Surface: #0c1b2f
- Accent primary: #58d5ff
- Accent secondary: #99ffbe

## Global Direction
- Lead with the daily decision, then the research evidence.
- Keep the home route product-facing and the sprint route operator-facing within one system.
- Use strong hierarchy between hero, decision strip, workbench sections, evidence, and risk boundary.

## Required State Model
- Every reviewed route should define loading, empty, partial, error, and success behavior.
- The first viewport should explain the page purpose and expose a primary next action.
- Desktop and mobile should preserve the same information hierarchy.

## Assumptions
## Route Contracts
- Route scope: /, /sprint-2
- Benchmark profile: finahunt_research_cockpit
- Review mode: auto
- Route scope was inferred or confirmed from browser_urls.

## Route Contracts

### /
- Intent: Help a first-time visitor understand the product, search quickly, and enter a discovery flow.
- Route kind: home
- Module order:
  - product thesis hero
  - date and refresh control rail
  - today focus summary
  - runtime and source overview
  - theme and event entry cards
  - workbench bridge CTA
- Required states: loading / empty / partial / error / success
- Notes:
  - Keep / opens with a clear hierarchy: purpose, browse affordance, proof, and next action all land above the fold.
  - Keep / feels like part of one continuous discovery-to-action journey.
  - Keep / keeps its hierarchy intact on desktop and mobile and preserves accessible structure.

### /sprint-2
- Intent: Expose the operational picture quickly and make the next decision obvious.
- Route kind: dashboard
- Module order:
  - research cockpit hero
  - view mode controls
  - decision strip
  - fermentation board
  - low-position research board
  - matrix and evidence views
  - risk and methodology boundary
- Required states: loading / empty / partial / error / success
- Notes:
  - Keep /sprint-2 opens with a clear hierarchy: purpose, browse affordance, proof, and next action all land above the fold.
  - Keep /sprint-2 feels like part of one continuous discovery-to-action journey.
  - Keep /sprint-2 keeps its hierarchy intact on desktop and mobile and preserves accessible structure.

## Accessibility Rules
- Preserve a meaningful heading order on every route.
- Do not rely on color alone for status or category meaning.
- Keep clear keyboard focus states for interactive elements.
