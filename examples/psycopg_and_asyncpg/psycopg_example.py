import os

import psycopg  # pip install psycopg>=3

from sqlcanon import Canonicalizer, Config

canon = Canonicalizer()
cfg = Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])


def exec_norm(cur, sql, params=None):
    # Normalise then execute a query.
    return cur.execute(canon.normalise(sql, cfg), params or ())


def main():
    dsn = os.getenv("POSTGRES_DSN")
    sql = "select 1 where 1 in (3,2,1) and 2=2"
    print("Normalised SQL:\n", canon.normalise(sql, cfg))

    if not dsn:
        print("POSTGRES_DSN not set; skipping DB execution.")
        return

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            exec_norm(cur, sql)
            print("Executed successfully against:", dsn)


if __name__ == "__main__":
    main()
