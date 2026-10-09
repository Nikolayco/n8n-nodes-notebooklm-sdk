# Vendored SDK

`notebooklm-sdk-0.3.5-nikolayco.1.tgz` is the `notebooklm-sdk` package used by this node.

- **Why it is here:** the official `notebooklm-sdk@0.3.4` still uses `notebooklm.google.com`, which Google now redirects to `notebook.google.com`
  (sign-in redirect loop, `CSRF token (SNlM0e) not found`, and `login` never finishing). The patched build fixes that.
  Keeping the file in this repository means the node no longer depends on a release that can disappear (the previous
  `v0.3.5-patch2` download URL returns 404).
- **Source:** release `v0.3.5` of https://github.com/darakcheeff/notebooklm-sdk (asset `notebooklm-sdk-0.3.4.tgz`,
  SHA-256 `c1b97a7ed52fe855c40c77749ca378a4eb45888a6561c7cf4acf4e4169df6ac5`) plus the video patch below.
- **SHA-256 of this file:** `caa666f1846568cef2f79733ab1c04ed0d570b885f2f9875105dc24ef138699b`
- **License:** MIT (the package contains its own `LICENSE`; upstream: https://github.com/agmmnn/notebooklm-sdk).
- **Changes in the darakcheeff build** (reviewed line by line, only `dist/` changes):
  - every `https://notebooklm.google.com` address became `https://notebook.google.com`;
  - the cookie filter was rewritten to match the host by domain rules (RFC 6265 style);
  - a desktop Chrome `User-Agent` header is sent with the page and RPC requests;
  - `login` accepts either host when waiting for the sign-in to finish. The old `notebooklm.google.com` name is still accepted there on purpose, as an alias.
- **Video patch added in this repository** (`vendor/patches/apply-sdk-patch.py`, applied to the build above), so that video generation
  sends the same request as [notebooklm-py](https://github.com/teng-lin/notebooklm-py) 0.8.x:
  - `VideoFormat.SHORT = 4` (vertical short-form video; its visual style is fixed by NotebookLM);
  - `VideoStyle` integer codes follow notebooklm-py (the old values sent Kawaii, Classic, Heritage, ... as the wrong style); `CUSTOM = 0`;
  - `createVideo` accepts `stylePrompt` (used with `style: CUSTOM`, Explainer/Brief only) and rejects the same invalid combinations notebooklm-py rejects; Cinematic sends no style;
  - `_callGenerate` replaces the legacy client options `[2]` with the full capability envelope the web client sends
    (some accounts get the generation refused with the short form, notebooklm-py #1594).
  - Verified offline against notebooklm-py: for every video format and style the request is identical
    (20 cases, CommonJS and ESM builds), and the invalid combinations raise errors.
- **Known issue (not fixed here):** the `login` helper does not wait for a sign-in on a browser profile that is not signed in yet,
  because `notebook.google.com` now serves a landing page to signed-out visitors instead of redirecting to the Google sign-in. It then fails with
  `Missing required cookie: SID`. Use notebooklm-py or a copied `Cookie` header instead (see the main README, Authentication).
- Cinematic (Veo 3) needs a Google AI Pro/Ultra plan and ignores the language setting (English voice-over).
- The node tarball built from this repository bundles this package (`bundleDependencies`), so installing the node does not download it again.
