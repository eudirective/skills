# Live test plan: distribution workflow

This plan checks the GitHub workflow after it is merged to `main`. The GitHub
workflow itself builds, validates, publishes, downloads, and checksum-checks the
release assets. No applicant data is used.

## Main branch release

1. Merge the reviewed change to `main` and open the **Package FreeMovement
   distributions** workflow run.
2. Confirm the run checks out the latest `main`, passes the distribution
   regression suite, builds twice with identical output, verifies all ZIPs,
   and checks `SHA256SUMS`.
3. Confirm `packages.json` contains one entry per marketplace plugin plus the
   two aggregate packages. For the current manifest, that is 34 ZIPs.
4. Confirm the run publishes the `freemovement-latest` prerelease and verifies
   the files by downloading them back and checking `SHA256SUMS`.
5. Confirm the release has the same archive count as `packages.json`, along
   with `packages.json` and `SHA256SUMS`, and has no obsolete ZIP assets.

## Source-library synchronization

1. Run **Build and sync FreeMovement source packages** on `main` after a source
   update, or wait for its scheduled run.
2. If it succeeds, confirm a **Package FreeMovement distributions** run starts
   from the current `main` snapshot. A failed mirror run must not publish.
3. Confirm the source-library archive includes all marketplace plugin source
   trees and the three provenance files, and that the source inventory hashes
   pass validation.
4. Confirm the package catalog records the `main` commit used for the build,
   while the source-library archive records the upstream revision from
   `component-index.json`.

## Failure handling

If a run fails, use its failing step as the reportable result. The workflow
artifact preserves the validated package set for 90 days once the build step
completes. Rerun after correcting the cause; do not report a successful live
release until the release download and checksum steps pass.
