# WORD RIVALS — Band III pilot 0.2

**Prepared for isolated online hosting, not yet deployed. No public game URL has been verified.**

Two real players compete for a 16-word territory board. Each gets six turns. Correct clues capture one or two words, including rival territory; complete rows and columns earn a bonus. There is no speed scoring. Definitions and examples appear after each move. The original 16 source-traceable Band III entries and game rules are unchanged.

## Build and test

Requires Node.js 22. No runtime packages need installing.

```sh
npm run build
npm test
node server.cjs
```

The local development address is `http://127.0.0.1:8787`. Use two separate browser profiles to test two player identities. The build creates `online.html` for the server and `demo.html` for two players sharing one device.

## Hosting gate

Read [DEPLOYMENT.md](DEPLOYMENT.md) and use `render.yaml` only in an authenticated hosting account, on the isolated `codex/word-rivals-online-20260928` branch. Public hosting requires managed HTTPS and `RENDER_EXTERNAL_URL` or `PUBLIC_ORIGIN`.

The intended host service uses free compute, automatic deploys off, no custom domain and no datastore. Account-specific billing/quota safeguards still require verification. The homepage, main branch, navigation and both Band III gates must not be changed.

## What is and is not verified

27 automated tests passed, including 100 simulated engine games and a functional check of 10 simultaneous rooms. The local offline HTML regression passed. Browser navigation to the local HTTP server was blocked by the environment, so a two-browser online session and physical-phone/public-host checks remain pending. This is not an audited production platform or a load-capacity claim.

Rooms live in memory and disappear after expiry or a server restart. No personal details, chat, app analytics or permanent profiles are collected. Spectator mode and cross-level balancing have not been implemented.

The original source provenance, full rules and historical 0.1 documentation are preserved in [README-pilot-0.1.md](README-pilot-0.1.md). Its old startup instructions describe 0.1; use the build commands above for 0.2.
