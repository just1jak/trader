import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INGEST_PATH = PROJECT_ROOT / 'congressional-trading' / 'congress_ingest.py'
DB_PATH = PROJECT_ROOT / 'congressional-trading' / 'congress_trades.db'


def sync_congressional_disclosures(
    year=None,
    start_year=None,
    end_year=None,
    limit=25,
    include_senate=False,
    all_history=False,
):
    module = _load_ingest_module()
    return module.sync_congressional_disclosures(
        year=year,
        start_year=start_year,
        end_year=end_year,
        limit=limit,
        include_senate=include_senate,
        all_history=all_history,
        db_path=DB_PATH,
    )


def congressional_disclosure_counts():
    module = _load_ingest_module()
    return module.disclosure_counts(db_path=DB_PATH)


def _load_ingest_module():
    spec = importlib.util.spec_from_file_location('congress_ingest', INGEST_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Could not load congressional ingest module at {INGEST_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
