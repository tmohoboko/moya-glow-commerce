# tmohoboko — Delivery control register
Audit date: 2026-10-17. Owner: [tmohoboko](https://github.com/tmohoboko).

This file is a cross-repository *tracking record*; it does not change deployments or imply release approval. Stored here because GitHub integration rejected writes to `software-delivery-portfolio` (HTTP 403) during this session.

## Repo inventory
| Repo | Classification | Current evidence | Next action |
|---|---|---|---|
| [moya-glow-commerce](https://github.com/tmohoboko/moya-glow-commerce) | Active: L Beauty storefront | 2026-10-09 clean build + 16/16 local regression; [CI success](https://github.com/tmohoboko/moya-glow-commerce/actions/runs/37910397155). Latest hosted L Beauty release **unverified**. | [#1 Hosted release gate](https://github.com/tmohoboko/moya-glow-commerce/issues/1); [#2 Manual QA](https://github.com/tmohoboko/moya-glow-commerce/issues/2); [#3 Enterprise API](https://github.com/tmohoboko/moya-glow-commerce/issues/3) |
| [software-delivery-portfolio](https://github.com/tmohoboko/software-delivery-portfolio) | Active: QA career portfolio | Historic 2026-09-26 production deploy, 10/10 smoke tests reported. Site still calls project earlier Moya Glow release. | Update truthfully with separate historic Moya Glow / present L Beauty evidence. **GitHub integration write 403; blocked** |
| [MTG.SoloSax](https://github.com/tmohoboko/MTG.SoloSax) | Reference / parked | 2020 sample-library commits by redtide; SFZ saxophone instruments, not confirmed as a new actively developed app. | Optional ownership/licence/playback audit, no speculative development |

## Sprint queue
- **WIP-1 / P0:** [L Beauty deploy identity and hosted regression #1](https://github.com/tmohoboko/moya-glow-commerce/issues/1). Done when deployment SHA/URL, hosted Playwright result and updated release gate are evidenced.
- **Blocked / P0:** Portfolio project card/evidence update. Unblock GitHub write access; preserve historic claims. Validate build and smoke before any deploy.
- **Ready / P1:** [L Beauty manual/cross-browser acceptance #2](https://github.com/tmohoboko/moya-glow-commerce/issues/2). Done on dated executed checks, defects/retests, and release assessment.
- **Backlog / P2:** [Persistent HTTPS FastAPI integration #3](https://github.com/tmohoboko/moya-glow-commerce/issues/3). Separate enterprise scope, not required to ship the static catalogue.
- **Parked / P3:** MTG.SoloSax maintenance investigation only.

## Control rules
1. Maximum **2 WIP implementation tasks**; do not begin a new project before checking current blockers.
2. **Done** = scoped output + traceable commit + relevant verification + evidence link + release gate, if applicable.
3. A Git push is **not** proof of Vercel deployment. Existing Vercel team scope in records is `tmdev`, independent of GitHub login `tmohoboko`; check project identity before any release. No deployments were done by this register.
4. Historic Sept 26 **Moya Glow** production 10/10 checks must never certify Oct 9 **L Beauty** changes.
5. 20-minute daily review: one next action, one verifiable artifact, update blockers. Weekly: throughput (accepted releases), proof, aged blockers and priorities.
6. Missing tmohoboko repositories for Dahprint, Royal Priesthood, Sashi, freelance services and QA practice are **intake candidates, not existing repos**. Prior `tmdev012/kanban-pmo` is untouched; no transfer or rename occurred.
7. No secrets, passwords, private CV content or sensitive job-search data in this public tracker.

## Sources
- [L Beauty release acceptance](../qa/RELEASE_ACCEPTANCE.md)
- [L Beauty current patch](../qa/FRONTEND_RELEASE_PATCH.md)
- [Portfolio release acceptance](https://github.com/tmohoboko/software-delivery-portfolio/blob/main/qa/RELEASE_ACCEPTANCE.md)

This inventory covers three repositories returned by the connected tmohoboko GitHub account; Vercel account contents were not independently enumerated.
