# Package distribution maintenance

## Release changelog

Update the repository-level `CHANGELOG.md` when shipped guidance, package identity, or bundled source-library content changes in a way package users can notice. Skip private tests, CI, and generated bookkeeping unless they change shipped content. Identify affected package versions; for coordinated national-package changes, link the versioned component index. Describe bundled legal material as a versioned snapshot, not a statement of current law.

Keep entries newest first, with a semantic version, date, affected package versions, and at least one concise user-facing change. The rolling distribution workflow validates the complete history and publishes the latest entry with the exact build revision and links to the full changelog, package manifest, and checksums.

The Discord announcement workflow runs only for `CHANGELOG.md` changes on `main`. It checks the newest entry against `freemovement-law/plugin.json`, skips edits that leave the newest entry unchanged, and posts through the repository Actions secret `DISCORD_WEBHOOK_URL`. It does not run for pull requests or manual dispatches.
