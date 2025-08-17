import asyncio
import os

import asyncpg  # pip install asyncpg

from sqlcanon import Canonicalizer, Config

canon = Canonicalizer()
cfg = Config(passes=["case_keywords", "sort_in_list", "normalise_predicates"])


async def exec_norm(conn: asyncpg.Connection, sql: str, *args):
    # Normalise then execute a query.
    return await conn.execute(canon.normalise(sql, cfg), *args)


async def main():
    dsn = os.getenv("ASYNC_PG_DSN")
    sql = "select 1 where 1 in (3,2,1) and 2=2"
    print("Normalised SQL:\n", canon.normalise(sql, cfg))

    if not dsn:
        print("ASYNC_PG_DSN not set; skipping DB execution.")
        return

    conn = await asyncpg.connect(dsn)
    try:
        await exec_norm(conn, sql)
        print("Executed successfully against:", dsn)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
