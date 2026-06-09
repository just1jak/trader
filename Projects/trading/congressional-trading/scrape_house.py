import argparse
from datetime import datetime

from congress_ingest import import_house_trades


def main():
    parser = argparse.ArgumentParser(description='Fetch House PTR filings and store parsed trades in SQLite.')
    parser.add_argument('--year', type=int, default=datetime.utcnow().year)
    parser.add_argument('--limit', type=int, default=25)
    args = parser.parse_args()
    print(import_house_trades(year=args.year, limit=args.limit))


if __name__ == '__main__':
    main()
