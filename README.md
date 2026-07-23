# SEIZURE project website

Website of the **SEIZURE** ANR project (ANR-24-CE45-4399): fusing MRI, PET and MEG with machine
learning to localize the epileptogenic zone in drug-resistant epilepsy and predict surgical outcome.

Live site: https://anr-seizure.github.io

The site is built with Jekyll and hosted on GitHub Pages. Almost everything you see is generated
from small data files in the `_data/` folder, so updating the site is usually just editing a
`.yml` file. You do not need to be a web developer.

---

## Where the content lives

| File | What it controls |
|------|------------------|
| `_data/project.yml` | Project facts, home page intro text, work packages, the partner logo row |
| `_data/institutions.yml` | Institution names, brand colors and logos (used by the chips and logo strip) |
| `_data/members.yml` | Members, grouped by lab, with role, institutions, thesis and scholarly ids |
| `_data/publications.yml` | Publications (filled automatically from HAL, plus any hand written entries) |
| `_data/openings.yml` | Open positions |
| `_data/news.yml` | Home page news feed |
| `_data/member_pubs.yml` | Generated per member publications (**do not edit by hand**) |

Photos go in `members/`, institution logos in `assets/logos/`, and publication figure thumbnails in
`images/publications/`.

---

## Making a change

### Option 1: edit on GitHub (no installation, easiest)

1. Open the repository on GitHub and go to the file you want to change (for example `_data/news.yml`).
2. Click the pencil icon (Edit this file).
3. Make your change, keeping the same indentation as the surrounding lines.
4. Scroll down and click Commit changes (commit to `main`, or open a pull request if you prefer a review).

GitHub Pages rebuilds the site automatically, usually within a minute. Refresh the live site to see it.

### Option 2: edit locally and preview first

Useful when you want to check a change before publishing. See [Preview locally](#preview-locally) below
for the one time setup, then edit the file, save, and the local preview reloads on its own.

---

## Common edits

**Add or update a member.** In `_data/members.yml`, add an entry under the right lab section. Only
`firstname` and `lastname` are required; the rest are optional and degrade gracefully.

```yaml
  - firstname: 'Jane'
    lastname: 'Doe'
    key: doe                      # short unique id, also links the auto publications
    role: 'PhD student'
    institutions: [creatis, cnrs] # keys from institutions.yml, first one colors the card
    picture: 'jDoe.jpg'           # file placed in members/
    interests: "graph signal processing, MEG"
    thesis:                       # for PhD students, shown instead of interests
      title: "Thesis title here"
      supervisors: "Carole Lartizien"
    idhal: "jane-doe"             # HAL author id (used to fetch their recent papers)
    orcid: "0000-0000-0000-0000"
    website: "https://example.org"
```

**Post a news item.** In `_data/news.yml`, add to the top of the list (newest first).

```yaml
  - date: "2026-09-01"
    title: "Paper accepted at MICCAI"
    blurb: "One sentence summary."
    tag: Publication               # Publication, Hiring, Milestone or Event
    url: "https://doi.org/..."     # internal path like /publications/ also works
```

**Open a position.** In `_data/openings.yml`, add an entry. Set `status: open` (or `auto` to derive
open/closed from `deadline`).

```yaml
  - title: "PhD on multimodal fusion"
    level: PhD                     # Master, PhD, Postdoc or Engineer
    wp: WP4
    lab: creatis                   # a key from institutions.yml
    location: "CREATIS, Lyon"
    duration: "3 years"
    start: "Autumn 2026"
    deadline: "2026-05-31"         # empty string "" if rolling
    status: open
    summary: "One or two sentences on the topic."
    profile: "Desired background."
    contact: "carole.lartizien@creatis.insa-lyon.fr"
    apply_url: "https://..."
```

**Publications** are handled automatically (see next section). To add one HAL does not know about,
add an entry to the relevant list in `_data/publications.yml` with `source: manual`.

---

## Publications, filled automatically from HAL

`scripts/fetch_hal.py` queries HAL for the project reference and for each member (by their idHAL or
ORCID), then writes `_data/publications.yml` and `_data/member_pubs.yml`. Hand written entries
(`source: manual`) and curated `figure:` thumbnails are always kept.

A GitHub Action (`.github/workflows/refresh-data.yml`) runs this every week and on demand, so the
publication list stays current on its own. To run it yourself:

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_hal.py
```

---

## Preview locally

This is optional. Most content edits are easier through [Option 1](#option-1-edit-on-github-no-installation-easiest).
A local preview needs Ruby and Jekyll. If you see `command not found: bundle` or `jekyll`, it means
this setup has not been done yet.

**One time setup.** On Ubuntu or Debian:

```bash
# 1. system Ruby and build tools
sudo apt-get update && sudo apt-get install -y ruby-full build-essential zlib1g-dev

# 2. install gems into your home folder so you never need sudo for gems.
#    (use ~/.bashrc instead of ~/.zshrc if your shell is bash)
echo 'export GEM_HOME="$HOME/.gems"' >> ~/.zshrc
echo 'export PATH="$HOME/.gems/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 3. Jekyll and Bundler
gem install jekyll bundler
```

On macOS: `brew install ruby`, make sure the Homebrew Ruby is on your `PATH`, then run
`gem install jekyll bundler`.

**Run it.** From the project folder:

```bash
bundle install                 # first time only, installs the pinned GitHub Pages gems
bundle exec jekyll serve
```

Open http://localhost:4000. The site reloads automatically when you save a data file.

**Troubleshooting.**

- `command not found: bundle` (or `jekyll`): the setup above has not run yet, or your shell has not
  picked up the new `PATH` (open a new terminal or run `source ~/.zshrc`).
- `undefined method 'tainted?'`: an old Jekyll (from an outdated `github-pages`) on modern Ruby
  (3.2+). The `Gemfile` pins a current `github-pages` (Jekyll 3.10) that works on Ruby 3.2+, so run
  `bundle install` (or `bundle update github-pages`) and try again.

---

## Repository layout

```
_data/           content you edit (see the table above)
_layouts/        page skeletons (base, page, home)
_includes/       reusable pieces (header, footer, cards)
assets/          css/, js/, fonts/, logos/
images/          project figures and publication thumbnails
members/         member photos
scripts/         fetch_hal.py, the HAL importer
tests/           unit tests for the importer
```

## Tests

```bash
PYTHONPATH=scripts python -m pytest tests/
```
