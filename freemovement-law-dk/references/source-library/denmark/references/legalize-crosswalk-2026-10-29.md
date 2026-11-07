# Denmark Legalize source crosswalk — 29 October 2026

## Result

The public Legalize index README at commit `abfba3a3c60f64aac3631225705b6ba32fc02965` lists Denmark’s `legalize-dk` repository and claims 45,400 norms. I checked the Denmark repository itself at its only commit, `5a678850e9ebb44d45b9bfd48e964ad1ac7f8264` (13 April 2026). The repository size is 0; that commit adds only `README.md` and an MIT `LICENSE`. The README describes intended Danish legislation in Markdown but contains no statutory files. Accordingly, this repository provides no retrievable Danish legal text to compare with Retsinformation and cannot be recorded as a Legalize retrieval method.

This is a verified finding about the checked public GitHub repository and commit; it does not establish that the Legalize website or sign-in MCP exposes no Danish content. That separate service was not used.

## Source-library overlap

The current Denmark pack manifest contains 16 national instruments. The following are among its overlapping legal texts for which a Legalize GitHub file was sought:

- Udlændingeloven, including the 2025 consolidation and 2026 amendments.
- Udlændingebekendtgørelsen and Visumbekendtgørelsen (2025).
- EU-opholdsbekendtgørelsen (2020) and its 2025 amendment.
- Forvaltningsloven (2014) and Offentlighedsloven (2020).
- Databeskyttelsesloven (2024), Retshåndhævelsesloven (2017), Arkivloven (2016), and Ombudsmandsloven (2013).
- Grundloven, Retsplejeloven, Udenrigstjenesteloven, foreign-service fees, Udlændingenævn rules, and the 2026 Schengen instruments.

No corresponding act file exists in the checked `legalize-dk` commit, so no Legalize text could be compared or copied. No Legalize method or conversion rule is assigned to these sources.

The Denmark source catalog separately identifies `Ansvar-Systems/Danish-law-mcp` at commit `84bac4d224e26d2d360c2950f354181b73f737be` as a pinned transport/conversion input, not an official publisher. This is not the Legalize repository and is not attributed as such here. Keep each official Retsinformation identity, currentness, and source-rights review in the existing source catalog and acceptance register. In particular, the catalog already identifies known later amendments to the 2025 Aliens Act consolidation and open currentness questions for older Danish consolidations; the empty Legalize repository does not resolve them.

## Evidence checked

- Legalize index: `legalize-dev/legalize` README at commit `abfba3a3c60f64aac3631225705b6ba32fc02965`.
- Country repository: `legalize-dev/legalize-dk`, default branch `master`, size 0.
- Only repository commit: `5a678850e9ebb44d45b9bfd48e964ad1ac7f8264`, whose changed-file list contains `README.md` and `LICENSE`, with no statute files.
- Official Danish source roster: `references/pack-manifest.json` (16 national instruments); currentness and official Retsinformation references remain in `references/source-catalog.json`.

No Danish Legalize source file was added to the national library because the repository contains no legal text to verify or attribute.
