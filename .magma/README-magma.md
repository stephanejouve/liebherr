# .magma/ — quality overlay for this fork

Ce dossier contient la surcouche de discipline "magma" appliquée au fork `bhuebschen/liebherr`. Il est **isolé** du custom_component HA lui-même (`custom_components/liebherr/`) pour que l'upstream soit merge-friendly.

## Contenu

- `pre-commit-config.yaml` — hooks pre-commit (black --line-length=100, ruff --fix, isort profile=black, trailing-ws, EOF, check-yaml)
- `pyproject.toml` — dev-only deps (pytest, pytest-asyncio, pytest-mock, black, ruff, isort, pre-commit, homeassistant helper)
- `ci-magma.yml` — GitHub Actions workflow séparé (lint + tests), destiné à `.github/workflows/ci-magma.yml`
- Ce README

## Setup dev local (une seule fois)

```bash
# Depuis la racine du repo
ln -sf .magma/pre-commit-config.yaml .pre-commit-config.yaml
ln -sf .magma/pyproject.toml pyproject.toml
poetry install
poetry run pre-commit install
```

Les symlinks au top-level sont **gitignored** — ils permettent aux outils (pre-commit, poetry, pytest) de trouver la config sans polluer les diffs upstream.

## Run manuel

```bash
poetry run pre-commit run --all-files
poetry run pytest tests/
```

## Rationale

Le fork est maintenu sous les standards de qualité de l'équipe magma (linting stricte, tests obligatoires pour nouvelle feature, TDD encouragé). Cette surcouche **ne s'impose pas à l'upstream** : si un jour bhuebschen mainstreame nos features, la PR n'inclut que le custom_component modifié + tests, pas le `.magma/` overlay.

Voir aussi `custom_components/liebherr/README.md` (upstream) pour la doc de l'intégration elle-même.
