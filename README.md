# freemovement plugin

**EU free-movement rights, grounded in legal sources and examined in practice.**

freemovement is a modular legal-research and consultation project focused on the rights of EU citizens and their family members. It combines an EU core with 31 separately installable jurisdiction packages. Its purpose is not simply to restate legislation, but to help users identify the applicable legal framework, examine how authorities apply it, and understand the procedural options available when rights are questioned or obstructed.

The project covers issues such as family-member entry visas, border entry, residence, administrative requirements, delays, refusals, and available remedies. It connects EU-level rules, case law, official guidance, and relevant national law, including related EEA and Swiss frameworks where supported. It also supports preventive reviews: identifying foreseeable procedural problems before an application or adverse decision.

The project is built around several principles:

- **Source-grounded analysis:** distinguish binding rules, official guidance, administrative practice, factual assertions, and unresolved legal questions; identify the source and its limitations.
- **Practical enforcement:** assess not only substantive rights but also appointments, document demands, interviews, processing, reasons for decisions, review procedures, complaints, and other means of enforcing those rights.
- **Modularity:** use an EU core plugin with independently installable jurisdiction-specific source packages, rather than requiring every national source library for every question.
- **Traceability and caution:** retain source provenance, version information, research gaps, and verification status. Bundled texts are snapshots, not a guarantee that the law remains current.

FreeMovement helps with research and preparation; it does not provide legal representation or guarantee a legal outcome. Experimental consultation and validation tools have their own limits and must not be treated as independent legal determinations.

## Install and use

The current packages primarily target **ChatGPT/Codex-compatible plugin and skill setups**. Installation depends on the capabilities of the host application. **Claude and other platforms may require adjustments** to manifests, instructions, directory layouts, or integration; compatibility with those hosts has not been verified.

Choose the form supported by your environment:

- **Plugin packages:** Visit [Releases](https://github.com/eudirective/skills/releases). The `freemovement-latest` entry points to a verified, revision-specific release containing downloadable ZIPs. Install the `freemovement-law` core and add only the relevant country plugins. Keep the extracted package directories together, using the directory names recorded in the [marketplace](marketplace.json), such as `freemovement-law-se/`.
- **Local checkout:** Use the same core and country directories directly from this repository. See the [core installation guide](freemovement-law/README.md#personal-installation) for the documented local plugin setup.
- **Skills without a plugin host:** A release also contains `freemovement-all-skills.zip`. Individual `SKILL.md` files and their supporting references can be adapted for platforms that support standalone skills but not the plugin architecture. Check relative paths and dependencies; copying a skill alone does not reproduce plugin-level registration or country routing.

After installation, **ask the plugin what it can do**. For example: *“List your available capabilities, modules, and workflows, including those that require explicit invocation.”* Some capabilities are deliberately not activated automatically and must be selected or requested expressly. You can also ask which country packages are installed and what sources are available for a particular procedure.

For current-law questions, verify the applicable text with its official publisher. The included legal material is a versioned snapshot; the [component index](component-index.json) records distribution versions and provenance, not legal currency or correctness.

## Repository map

| Location                                                           | Purpose                                                                           |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| [`freemovement-law/`](freemovement-law/)                           | EU core plugin, shared sources, consultation workflows, and supporting tools      |
| `freemovement-law-xx/`                                             | Separately installable jurisdiction packages, including national source libraries |
| [`scripts/source-distribution/`](scripts/source-distribution/)     | Source registry, templates, generation, and version checks                        |
| [`scripts/package-distributions/`](scripts/package-distributions/) | ZIP packaging, verification, and release tooling                                  |
| [`.github/workflows/`](.github/workflows/)                         | Source synchronization, tests, release publication, and announcements             |

The [marketplace](marketplace.json) lists registered plugins, the [component index](component-index.json) records versions, and the [changelog](CHANGELOG.md) describes user-facing changes. Canonical source records and module notes are maintained in [eudirective/public-data](https://github.com/eudirective/public-data).

## Contributing and development branches

Bug reports, documentation problems, missing sources, and feature proposals can be submitted through the [issue tracker](https://github.com/eudirective/skills/issues).

**Direct contributions require prior onboarding and acceptance of the project's specific Contributor License Agreement (CLA).** Contact the maintainers before submitting a code or documentation pull request. The issue tracker is available for suggestions and reports without direct repository contributions.

`main` is the published-code reference. `testing`, `development`, or other registered development branches may be available for work in progress or upcoming features; their contents and relationship to `main` should be checked rather than assumed.

## Source maintenance

Change a file at its owning source, not merely in a generated copy:

- Maintain canonical legal-source records and module notes in [`eudirective/public-data`](https://github.com/eudirective/public-data).
- Maintain country registration, generated package templates, and distribution rules in [`scripts/source-distribution/`](scripts/source-distribution/).
- Maintain EU core instructions and consultation tooling in [`freemovement-law/`](freemovement-law/).

Source synchronization uses a recorded upstream revision and regenerates packages, indexes, and provenance metadata. Changes made only to generated national package files can be overwritten. Keep the root and host-facing marketplace manifests consistent, and record user-facing package changes in the [changelog](CHANGELOG.md).

To stage a new source distribution from a matching local `eudirective/public-data` checkout at `../public-data`:

```sh
stage="$(mktemp -d)"
revision="$(git -C ../public-data rev-parse HEAD)"
python3 scripts/source-distribution/build.py \
  --source-root ../public-data/source-library \
  --module-notes-root ../public-data/module-notes \
  --registry scripts/source-distribution/country-registry.json \
  --upstream-revision "$revision" \
  --plugin-root freemovement-law \
  --previous-root . --output-root "$stage"
```

Review the staged output before applying it. The [source synchronization workflow](.github/workflows/mirror-source-library.yml) documents the automated stage-and-apply process.

## Testing and verification

The repository provides separate regression suites for source distribution, packaging, and the consultation tools, plus a standalone consultation self-test and generated-version validation. A local development environment can run the same essential checks as CI:

```sh
python3 -m pip install -r freemovement-law/requirements-test.txt
export PYTHONDONTWRITEBYTECODE=1

python3 -m unittest discover -s scripts/source-distribution -p 'test_*.py'
python3 -m unittest discover -s scripts/package-distributions -p 'test_*.py'
python3 -m unittest discover -s freemovement-law/skills/eudirective-core/scripts -p 'test_*.py'
python3 freemovement-law/skills/eudirective-core/scripts/run_selftest.py
python3 scripts/source-distribution/validate_versions.py \
  --root . --registry scripts/source-distribution/country-registry.json
```

Run from the repository root, using Python 3.12 to match CI. Setting `PYTHONDONTWRITEBYTECODE=1` helps prevent local Python cache files from entering generated packages or affecting fingerprints. CI also validates source synchronization and the exact revision before publishing from `main`.

These checks establish specified code, archive, and metadata properties. They do **not** establish that an individual legal conclusion is correct, that bundled legislation is current, or that a host application will invoke every available workflow automatically.

## Building distribution ZIPs

The package builder produces individual plugin ZIPs, an all-skills ZIP, a source-library ZIP, a package catalog, and checksums. Build into a directory **outside** the repository:

```sh
out="$(mktemp -d)/distributions"
python3 scripts/package-distributions/build.py all --root . --output-dir "$out"
python3 scripts/package-distributions/build.py verify --root . --distribution-dir "$out"
```

The publication pipeline checks reproducibility and the exact source revision. Published distribution assets are attached to revision-specific releases; [`freemovement-latest`](https://github.com/eudirective/skills/releases/tag/freemovement-latest) points to the latest verified release. The pointer itself need not contain downloadable ZIPs.

## Licence and third-party material

See the project-wide [eudirective Personal and Institutional Licence (EPIL)](LICENCE.md) for permissions and restrictions on covered material. Official legal sources and third-party assets retain their own rights and conditions; bundled attribution and third-party licence notices remain applicable.
