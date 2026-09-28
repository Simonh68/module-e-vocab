# WORD RIVALS 0.2 — isolated online pilot handoff

## Current status

Prepared and tested locally; **not deployed**. There is no verified public game URL.
The connected tools do not currently include an authenticated hosting service. Render was offered as a connection; it has not been assumed installed or authorized. GitHub CLI networking is unavailable here; repository operations use the authenticated GitHub connector.

The approved scope is an independently hosted Band III two-player pilot with a shareable room link. Do not add it to the homepage, main navigation, sitemap, either Band III gate, or any existing production deployment. Do not change DNS. Cross-level balancing and spectator consent/read-only viewing remain separate, unimplemented work.

## Reproducible build and local run

```sh
cd pilots/word-rivals
npm run build
npm test
node server.cjs
```

No `npm install` or runtime third-party packages are required. Node 22 was used for the tests. `index.html` remains the original audited offline source. `build-online.cjs` derives `online.html` with the 0.2 transport UI; it does not embed the offline answer engine. `demo.html` remains the original same-device demo. Generated HTML files are not required in Git: the build recreates them.

## Proposed Render deployment, only after account connection

Use the new branch `codex/word-rivals-online-20260928` in `Simonh68/module-e-vocab`, not `main`. The Blueprint is at `pilots/word-rivals/render.yaml`; specify this path explicitly when setting up a Blueprint. Alternatively create one Node web service with these exact settings:

- Root directory: `pilots/word-rivals`.
- Build: `node build.cjs && node build-online.cjs && node --test tests/*.test.cjs`.
- Start: `node start-public.cjs`.
- Health check: `/health`.
- Region: Frankfurt; compute plan: **Free**; automatic deploys: **off**.
- Node version: `22`; `NODE_ENV=production`.
- No custom domain, databases, disk, cron task, analytics, or background keep-alive.

`start-public.cjs` listens on `0.0.0.0` and the provider's `PORT`. It uses the provider's `RENDER_EXTERNAL_URL` as the canonical HTTPS origin; another managed host must set `PUBLIC_ORIGIN`. Startup fails if this is absent or not a bare HTTPS origin. No credentials belong in the repository or chat.

Before creation, inspect the actual workspace/plan and any existing similarly named service. Create a new isolated service; do not overwrite another service. Confirm free compute and account billing/quota safeguards. A free compute plan does not prove that an account with a payment method cannot incur usage charges. No paid plan or charge is authorized.

After deployment, read the provider-returned URL and deployment status, check `/health` for 0.2.0, then run two browsers and two physical phones over distinct networks. Verify invitation, joins, equal turns, reload, disconnect/reconnect, final scores, and rematch. Do not report success from a build alone. Verify production HTTPS cookies, actual proxy headers, and response streaming on that host.

## Hardening and operational limits

Public mode sets Secure + HttpOnly + SameSite=Strict room cookies even behind an HTTPS ingress. Requests must use the configured Host and Origin; forged forwarding headers are not trusted. All game responses request no indexing and no caching. Inline scripts are authorized by content hashes rather than `unsafe-inline`. `/robots.txt` disallows crawling; this is not access control.

Room codes now contain 12 random hexadecimal characters. Separate secret player cookies are never placed in invitation links. Room state has a monotonic revision to ignore stale client updates. New JSON fields and bodies above 2 KiB are rejected. Admission limits use global counters (60 room creations / minute, 240 join attempts / minute), not IP addresses or fingerprints. A default 100-room cap includes lobbies and completed rooms; it is not a tested 200-player capacity promise. Slow event-stream clients have a bounded output queue. No application request log is written.

This remains a single-process, memory-only pilot. Rooms expire after 30 minutes without a game action or two hours at most, with cleanup on requests or at the next cleanup interval. Restart, redeploy or host sleep loses rooms. Normal shutdown notifies connected clients, who must open a new room. It is not a persistent public game platform. Hosting infrastructure may process technical network data independently of the application's no-analytics policy.

Render documents idle spin-down for free web services after 15 minutes without inbound traffic, a cold start on the next request, ephemeral files, and shared free quotas. Do not keep the service artificially awake or describe this as an always-on service. Paid hosting or durable room storage requires a separate decision.

## Verification from this work

- `npm run build` passed; `npm test`: **27/27** passed.
- Includes the original 100 complete simulated engine games, full HTTP/SSE match and rematch, expiry and reconnect checks.
- Added HTTPS-origin/cookie tests, script-hash and crawler-header tests, JSON/privacy boundary tests, admission limits, room cap, concurrent join race, and **10 simultaneous rooms / 20 synthetic player sessions** with isolated event streams. This is a functional concurrency check, not a load benchmark.
- Local offline HTML UI regression passed through 12 turns and at 390 px width. The online UI is mechanically derived; scripts compile and the exact served page is covered by HTTP/header tests.
- The attempt to navigate Chromium to the local HTTP server was blocked with `ERR_BLOCKED_BY_ADMINISTRATOR`. No bypass was attempted. No successful browser-to-server, public-hosting, or physical-phone check is claimed. `tests/browser_online.py` is prepared for an authorized environment and reports this failure explicitly.
- No homepage, source vocabulary, Band III gate, DNS, public deployment, or billing change was made.

## Official provider references checked for this preparation

- https://render.com/docs/your-first-deploy
- https://render.com/docs/blueprint-spec
- https://render.com/docs/environment-variables
- https://render.com/docs/free
- https://render.com/docs/faq

These references inform the proposed configuration; provider validation and account-specific limits are still pending.
