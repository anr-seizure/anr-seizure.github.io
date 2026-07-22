# SEIZURE project website

Website of the **SEIZURE** ANR project (ANR-24-CE45-4399): fusing MRI, PET and MEG with machine
learning to localize the epileptogenic zone in drug-resistant epilepsy and predict surgical outcome.

Built with Jekyll (GitHub Pages compatible). Content is data driven, so most updates are a YAML edit.

## Updating content

Everything visible on the site is driven by files in `_data/`:

| File | What it controls |
|------|------------------|
| `_data/project.yml` | Project facts, hero text, work packages, partner list |
| `_data/institutions.yml` | Institution names, brand colors and logos (chips and partner strip) |
| `_data/members.yml` | Members, grouped by lab, with roles, institutions, thesis and scholarly ids |
| `_data/publications.yml` | Publications (auto from HAL, plus hand written `source: manual` entries) |
| `_data/openings.yml` | Open positions |
| `_data/news.yml` | Home page news feed |
| `_data/member_pubs.yml` | Generated per member publications (do not edit by hand) |

Edit the relevant file, commit and push. To add a member from a new institution, add an entry to
`institutions.yml` and reference its key in `members.yml`.

## Publications, automatic from HAL

`scripts/fetch_hal.py` queries HAL for the project reference and for each member (by idHAL or ORCID)
and writes `_data/publications.yml` and `_data/member_pubs.yml`. Hand written entries
(`source: manual`) and curated `figure:` thumbnails are preserved across refreshes.

Run it locally:

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_hal.py
```

The GitHub Action in `.github/workflows/refresh-data.yml` runs it weekly and on manual dispatch,
committing any changes. Enable Actions on the repository to use it.

## Running the site locally

```bash
bundle install
bundle exec jekyll serve
```

Then open http://localhost:4000.

## Tests

```bash
PYTHONPATH=scripts python -m pytest tests/
```
