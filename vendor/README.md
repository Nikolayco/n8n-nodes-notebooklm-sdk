# Vendored SDK

`notebooklm-sdk-0.3.5-darakcheeff.tgz` is the `notebooklm-sdk` package used by this node.

- **Why it is here:** the official `notebooklm-sdk@0.3.4` still uses `notebooklm.google.com`, which Google now redirects to `notebook.google.com`
  (sign-in redirect loop, `CSRF token (SNlM0e) not found`, and `login` never finishing). The patched build fixes that.
  Keeping the file in this repository means the node no longer depends on a release that can disappear (the previous
  `v0.3.5-patch2` download URL returns 404).
- **Source:** release `v0.3.5` of https://github.com/darakcheeff/notebooklm-sdk (asset `notebooklm-sdk-0.3.4.tgz`, unmodified).
- **SHA-256:** `c1b97a7ed52fe855c40c77749ca378a4eb45888a6561c7cf4acf4e4169df6ac5`
- **License:** MIT (the package contains its own `LICENSE`; upstream: https://github.com/agmmnn/notebooklm-sdk).
- **Difference from the official 0.3.4 build** (reviewed line by line, only `dist/` changes):
  - every `https://notebooklm.google.com` address became `https://notebook.google.com`;
  - the cookie filter was rewritten to match the host by domain rules (RFC 6265 style);
  - a desktop Chrome `User-Agent` header is sent with the page and RPC requests;
  - `login` accepts either host when waiting for the sign-in to finish.
  No new network destinations, no `child_process`, `eval` or dynamic imports were added.
- The node tarball built from this repository bundles this package (`bundleDependencies`), so installing the node does not download it again.
