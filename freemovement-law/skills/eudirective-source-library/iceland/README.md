Skill: author-source-pack-rules v1.0.1

# Iceland source candidates

Iceland's first-pass discovery is recorded in the [candidate manifest](references/candidate-manifest.json) and [source list](references/source-list.md). Iceland is an EEA EFTA State, not an EU Member State. A shared bounded capture/replay pass saved 21 responses and converted 20 local copies for review; none is accepted. Six Althingi requests returned 403, one court-rules page returned 404, and an Ombudsman landing page had no extractable body. The Althingi index reports a dated current Lagasafn edition, which can be reviewed as an official reference; the unresolved SGML route affects local capture only. Record the edition cutoff and use Gazette items only for a known material issue.

Run `python source-library/sync_candidate_pages.py iceland sync` to refresh the listed pages and `python source-library/sync_candidate_pages.py iceland verify` to replay saved conversions offline. No Iceland-specific SGML importer or archive-change rule is implemented. See the [sustainability assessment](references/sustainability-assessment.md) for remaining archive, amendment, Regulation 540/2017, and service-page issues.
