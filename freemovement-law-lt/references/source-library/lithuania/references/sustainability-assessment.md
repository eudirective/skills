# Lithuania source-rule sustainability assessment

Assessment date: 21 October 2026; local-text promotion and card-order identity correction: 25 October 2026. Scope: the official links and local text snapshots recorded in `source-list.md` and `source-acceptance.json`. This assesses source usability and optional retained-copy routes, not legal advice, topic completeness, or country completion.

## Official source routes

The Register of Legal Acts (e-TAR), maintained by the Seimas Chancellery, is the official legal publication and consolidated-text reference. The Lithuanian Open Data Portal TAR dataset is a separate API route that exposes document metadata, version intervals and Lithuanian text. The portal entry lists CC BY 4.0 for that dataset; attribution is included in each local snapshot. That licence does not extend to unrelated e-TAR pages, agency guidance, forms, court decisions or mission content.

Thirteen API text snapshots are accepted as local historical/versioned documents under `../documents/legislation/`. Their source-response hashes, version-metadata hashes, conversion hashes, API version IDs and effective intervals are recorded in each file and in the source-acceptance evidence. An open-ended interval reported by the dataset is preserved as dataset metadata only; it is not a finding that the text is the current consolidated law. The two converted HTML pages (N-Lex country information and the dataset description) remain link-only references because they are discovery/catalogue pages rather than national legal texts.

## Currentness and identity findings

The API version selector is not reliable enough to establish current law in the observed records. Examples include:

- The Aliens Law API snapshot begins 2026-01-01 while e-TAR showed a 2026-07-01 to 2026-10-31 consolidated edition on the 21 October source review.
- The Public Administration Law API snapshot begins 2024-01-01 while e-TAR showed a 2026-10-01 to 2026-12-31 edition.
- The two family-card API texts are not current: they are former Orders 1V-290 and 1V-369, valid in the captured consolidated versions from 1 March through 30 June 2019 and repealed from 1 July 2019.
- The current combined card procedure is Interior Minister Order 1V-594, official e-TAR record `e1cacab099a811e9ae2e9d61b1f977b3`, consolidated from 5 April 2023 onward at the 25 October check; it covers both temporary and permanent cards.
- The Civil Status Registration, Ombudsmen, personal-data protection and legal-aid API versions also predate later e-TAR dates recorded in the source register.

The 13 local documents are therefore useful as exact dated source texts and historical evidence, not as a synchronized current-law corpus. Consult the live e-TAR `/asr` record for the relevant date. The broad Aliens Law has a distinct EU residence regime; keep EU free movement, EFTA/Swiss treaty rights, UK Withdrawal Agreement cases and third-country family reunification separate.

## Acquisition and maintenance limits

The retired `sync_lithuania.py` wrote to a removed working location and selected a dataset API version using metadata already shown to conflict with e-TAR. No recurring updater or Lithuania Monitor runtime action is supported in this environment. The script was removed rather than left as a misleading currentness tool. Runtime retrieval, automated version selection, conversion replay and ongoing update detection are unsupported, not completed.

Direct e-TAR requests returned HTTP 403 to the earlier research client. This is a client access limitation, not evidence of a publisher-wide outage. Do not bypass access controls. The API's pagination, change-feed and schema stability have not been validated for recurring monitoring. The LITEKO search surface remains selective discovery, not a complete judgments corpus or change feed.

## Remaining work

Eleven source records remain pending human or currentness review. Provision-level topic mapping, dynamic Migration Department/MFA forms and mission routes, decision-specific remedies, continuing case-law discovery, and operational validation remain open. The 37 accepted official links and 13 dated text snapshots do not establish topic adequacy or completion for Lithuania.
