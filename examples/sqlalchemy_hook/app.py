from sqlalchemy import create_engine, event, text

from sqlcanon import Canonicalizer, Config

# In-memory SQLite for a zero-dependency demo
engine = create_engine("sqlite+pysqlite:///:memory:", future=True)

canon = Canonicalizer()
cfg_exec = Config(passes=["case_keywords", "sort_in_list", "normalize_predicates"])


@event.listens_for(engine, "before_cursor_execute")
def normalise_before_execute(conn, cursor, statement, parameters, context, executemany):
    norm = canon.normalise(statement, cfg_exec)
    if norm != statement:
        print("— SQL normalised —")
        print(norm)
    return norm, parameters


def main():
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t(a INTEGER, b INTEGER, c TEXT)"))
        conn.execute(text("INSERT INTO t(a,b,c) VALUES (1,1,'x'), (2,1,'y'), (3,2,'z')"))
        # Intentionally messy SQL to show the effect
        result = conn.execute(text("select a FROM t where b=1 and a in (3,2,1) and c='x'"))
        rows = result.fetchall()
        print("Rows:", rows)


if __name__ == "__main__":
    main()
