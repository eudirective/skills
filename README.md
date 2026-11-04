# FreeMovement skills and source plugins

FreeMovement provides source-grounded EU free-movement and EU-family-visa
guidance through an EU core plugin and 31 separately installable national source
plugins. Install the core and add the national packages relevant to your work.

This repository contains the distributed skills, bundled source snapshots,
synthetic consultation-engine tooling, and scripts that build and validate the
distribution. Canonical source records are maintained in
[eudirective/public-data](https://github.com/eudirective/public-data).

## Start here

- [Core plugin guide](freemovement-law/README.md): capabilities, requirements,
  personal installation, and consultation output.
- [Core skill](freemovement-law/skills/eudirective-core/SKILL.md): consultation
  routing and source-use instructions.
- [Marketplace](marketplace.json): available plugins and their repository paths.
- [Component index](component-index.json): exact component versions,
  compatibility metadata, and source fingerprints.
- [Changelog](CHANGELOG.md): user-visible package and guidance changes.

## Installation and use

Use a host with plugin and skill support. Follow the personal installation
instructions in the [core plugin guide](freemovement-law/README.md#personal-installation)
to register the core in your local marketplace, then add the relevant country
packages using the entries in this repository's marketplace.

Keep country packages beside the core using their repository directory names,
such as `freemovement-law-se/`.

Bundled sources are versioned snapshots. Installation does not synchronize them
with their publishers. Claims that depend on current law require checking the
responsible official publisher and identifying the version or date checked.
Package version checks establish metadata status, not legal correctness or
source currentness.

Real applicant accounts may be discussed in chat under the skill's instructions.
The consultation-engine scripts are for synthetic or explicitly permitted
abstract records; do not put real applicant facts into synthetic fixtures or
distributable assets. The plugin provides informational guidance, not legal
representation or a guaranteed outcome.

## Repository layout

| Path | Purpose |
| --- | --- |
| `freemovement-law/` | EU core plugin, skills, source library, contracts, and synthetic engine tests |
| `freemovement-law-xx/` | Generated country plugins, using two-letter country codes |
| `scripts/source-distribution/` | Source distributor, country registry, templates, operational modules, and version validation |
| `scripts/package-distributions/` | Archive builder, verification, release notes, and announcement tooling |
| `.agents/plugins/marketplace.json` | Host-facing plugin marketplace |
| `marketplace.json` | Root marketplace copy; must match the host-facing copy |
| `component-index.json` | Component versions and provenance metadata |
| `source-inventory.json` | Source classification and distribution records |
| `migration-map.json` | Source-to-distribution mapping |
| `.github/workflows/` | Validation, source synchronization, packaging, and release automation |

## Development setup

Run the commands below from the repository root. Python 3.12 matches CI.
Python consultation validators require `jsonschema`; the distribution tooling
uses the Python standard library. Node.js 18 or later is needed for the optional
session version-check scripts.

Create a virtual environment outside the package directories so that local
dependencies are not included in distributed archives:

```sh
python3 -m venv ../freemovement-venv
. ../freemovement-venv/bin/activate
python -m pip install -r freemovement-law/requirements-test.txt
export PYTHONDONTWRITEBYTECODE=1
```

Disabling bytecode generation keeps `__pycache__` files out of the package trees
and their content fingerprints.

## Validation

Run each suite separately; both distribution directories contain a module
named `build.py` and a test module named `test_build.py`.

```sh
python -m unittest discover -s scripts/source-distribution -p 'test_*.py'
python -m unittest discover -s scripts/package-distributions -p 'test_*.py'
python -m unittest discover -s freemovement-law/skills/eudirective-core/scripts -p 'test_*.py'
python freemovement-law/skills/eudirective-core/scripts/run_selftest.py
python scripts/source-distribution/validate_versions.py \
  --root . \
  --registry scripts/source-distribution/country-registry.json
```

The standalone self-test is not included in `unittest` discovery. At the
2026-11-02 repository review, the 223 discovered tests and 32-component version
check passed, while the standalone self-test failed at the Visa Code candidate
disposition assertion. Treat that as an unresolved test/implementation
disagreement, not a successful validation run.

The PR workflow currently runs source-distribution tests and version validation.
The packaging workflow additionally runs package-distribution tests. Neither
currently runs the consultation suite or standalone self-test, so run these
locally when changing consultation behavior.

Local tests check synthetic behavior and artifact contracts. They do not prove
legal correctness or enforce ordinary hosted assistant answers. See the
[host-boundary status](freemovement-law/skills/eudirective-core/references/consultation-controlled-release-live-test-plan.md).

## Making changes

Edit the owning source rather than only its generated copy:

- Maintain canonical source records and module notes in `eudirective/public-data`.
- Maintain country registration, generated skill instructions, templates, and
  packaged operational modules in `scripts/source-distribution/`.
- Maintain core instructions and engine code under `freemovement-law/`.
- Regenerate country packages and provenance indexes after changing their
  inputs. Direct changes to generated country content can be overwritten by
  source synchronization.

Use the distributor to reconcile generated manifests and fingerprints. Do not
manually change a hash merely to make validation pass. Keep both marketplace
copies identical when applying a generated stage, and describe user-visible
changes in `CHANGELOG.md`.

### Generate a source distribution

With a checkout of `eudirective/public-data` at `../public-data`, build into a
fresh temporary directory:

```sh
source_stage=$(mktemp -d)
upstream_revision=$(git -C ../public-data rev-parse HEAD)
python scripts/source-distribution/build.py \
  --source-root ../public-data/source-library \
  --module-notes-root ../public-data/module-notes \
  --registry scripts/source-distribution/country-registry.json \
  --upstream-revision "$upstream_revision" \
  --plugin-root freemovement-law \
  --previous-root . \
  --output-root "$source_stage"
```

The output directory must be empty. Use an upstream checkout whose files match
the recorded revision. Review the staged packages and metadata before applying
them to this repository. The
[source synchronization workflow](.github/workflows/mirror-source-library.yml)
shows the automated stage-and-apply process.

### Build downloadable archives

Build from a validated repository snapshot, with output outside the package
directories:

```sh
distribution_parent=$(mktemp -d)
distribution_dir="$distribution_parent/distributions"
python scripts/package-distributions/build.py all \
  --root . --output-dir "$distribution_dir"
python scripts/package-distributions/build.py verify \
  --root . --distribution-dir "$distribution_dir"
```

The builder produces individual plugin ZIPs, aggregate skill and source-library
archives, `packages.json`, and `SHA256SUMS`. CI builds twice and compares the
results before publishing the rolling prerelease. These local commands do not
publish a release.

## Use and licensing

The plugin is intended for personal use. Non-personal use—including use for an
employer, organization, client, paid service, or deployment for others—requires
a license. Request one at eudirective@proton.me. See the
[core plugin's use terms](freemovement-law/README.md#use-and-licensing).
Bundled third-party assets retain their accompanying attribution and license
files.
