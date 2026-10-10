# RepoFlow — Backend

API FastAPI de RepoFlow. Voir le [README principal](../README.md) pour
l'installation complète.

## Développement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Documentation interactive : http://localhost:8000/docs
