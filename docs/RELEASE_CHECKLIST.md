# M7 portfolio release checklist

**M2 verified complete (2026-10-04):** [five-company controlled load evidence](M2_FIVE_COMPANY_LOAD_STATUS.md) and [post-load checks](M2_POST_LOAD_VERIFICATION.json) supersede the historical preparation queues.

A checked item must have evidence. Do not mark an external/runtime item complete because the repository implementation merely exists.

## Data readiness — blocking

Selected core history is reviewed and loaded: 629 facts, 46 explicitly withheld conflicts and two unavailable printed dashes. Coverage limitations and the Tata FY2024 gap are recorded in the linked verification evidence.
- [x] Verified primary filings selected for all five initial companies
- [x] Approximately five years of financial history reviewed where available
- [x] Reporting periods, currency, units, and source provenance verified
- [x] Conflicting source values resolved or explicitly recorded
- [x] No fabricated production financial data
- [x] Verified data loaded into the target Supabase project

## Repository quality

- [x] M0 foundation implemented
- [x] M1 schema/RLS foundation implemented
- [x] M3 deterministic analytics implemented
- [x] M3 controlled reported-policy publisher, SQL input/arithmetic guards, atomic receipts, recovery and frontend evidence bindings implemented — [workflow and coverage](M3_CONTROLLED_PUBLICATION.md)
- [x] M3 native production publication and receipt independently verified — [43 metrics / one signal / 32 unavailable](M3_PUBLICATION_VERIFICATION.md)
- [x] M4 local source-backed AI pipeline and controlled review/publication workflow implemented — [operator guide](M4_CONTROLLED_PUBLICATION.md)
- [ ] M4 actual local model generation, exact human AI reviews, native publication receipts and browser evidence rendering independently verified
- [x] M5 interactive static frontend implemented
- [x] M6 security/frontend integration merged with green CI
- [x] M2 verified-data population complete
- [ ] Final release-commit CI green

## Supabase production verification — blocking

- [ ] All migrations applied in order
- [x] Provenance migration preflight reviewed; legacy demotion/derived-output blockers addressed — [live evidence](SUPABASE_VERIFICATION.md)
- [x] Private ingestion schema excluded from Data API; review/function grants verified — [live evidence](SUPABASE_VERIFICATION.md)
- [ ] Reviewed publication guards and target concurrency/retry behavior verified
- [x] Publisher schema inventory inspected; plan/schema hashes reviewed before explicit apply
- [ ] Live lock contention/timeouts, receipt replay and uncertain-COMMIT recovery verified
- [x] Controlled load receipt and resulting approved records retained as evidence
- [x] RLS enabled on every exposed table in the target project — [live evidence](SUPABASE_VERIFICATION.md)
- [ ] Browser anon SELECT succeeds only for intended public data
- [x] Browser anon INSERT fails on every exposed table — live SQL role probes
- [x] Browser anon UPDATE fails on every exposed table — live SQL role probes
- [x] Browser anon DELETE fails on every exposed table — live SQL role probes
- [ ] AI insight visibility follows the validated/verified-source policy
- [ ] Privileged credential exists only in the controlled local pipeline environment

## Cloudflare Pages — blocking

- [ ] Pages project connected to `main`
- [ ] Build output set to `web`
- [ ] Production deployment succeeds
- [ ] `Content-Security-Policy` is present in real responses
- [ ] Referrer/MIME/permissions headers are present in real responses
- [ ] No privileged credential is present in deployed JavaScript
- [ ] Public site works without Ollama running

## Functional verification

- [ ] Home page and company search work
- [ ] Populated company workspace renders verified data
- [ ] Financial trends display correctly
- [ ] Deterministic metrics display correctly
- [ ] Red flags are labelled as investigation signals
- [ ] AI insights display only validated text
- [ ] Evidence links point to approved HTTPS sources
- [ ] Missing data produces an explicit unavailable/empty state
- [ ] Peer snapshot behaves correctly for the limited V1 universe

## Browser/accessibility verification

- [ ] Keyboard-only navigation tested
- [ ] Visible focus states verified
- [ ] Mobile/responsive layout checked
- [ ] Reduced-motion preference checked
- [ ] No significant console errors
- [ ] No blocked legitimate requests caused by CSP

## Portfolio assets

- [x] Architecture documentation
- [x] Mermaid architecture diagram
- [x] Demo walkthrough
- [x] Deployment runbook
- [ ] Production screenshots captured after real data/deployment verification
- [ ] Final README updated with live deployment link only after deployment exists

## Release decision

Release may be described as **portfolio-ready / deployed** only after every blocking item above is checked with evidence. Until then, the honest status is **repository implementation complete through M6 and M2 selected history loaded/verified; derived runtime outputs and production deployment verification pending**.
