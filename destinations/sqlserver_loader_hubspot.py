import pandas as pd
from sqlalchemy import create_engine
import pyodbc

# def load_to_sql(df: pd.DataFrame, table_name: str, connection_string: str):
#     engine = create_engine(connection_string)
#     with engine.begin() as conn:
#         df.to_sql(table_name, con=conn, if_exists="replace", index=False)

def map_dtype(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return "INT"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    else:
        return "NVARCHAR(MAX)"



def load_to_sql_hubspot_api(df: pd.DataFrame, table_name: str, connection_string: str, load_mode: str):
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    cols = [col.replace('.', '_') for col in df.columns]
    columns_sql = ",\n".join([f"[{col.replace('.', '_')}] {map_dtype(dtype)}" for col, dtype in df.dtypes.items()])

    if not columns_sql.strip():
        raise ValueError("No columns defined for table creation")

    create_table_sql = f"""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
    BEGIN
        CREATE TABLE [{table_name}] (
            {columns_sql}
        )
    END
    """
    cursor.execute(create_table_sql)
    conn.commit()

    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f"INSERT INTO [{table_name}] ({', '.join(f'[{c}]' for c in cols)}) VALUES ({placeholders})"

    if load_mode.lower() == 'full':
        cursor.execute(f"DELETE FROM [{table_name}]")
        conn.commit()
        print(f"Table {table_name} truncated for full reload.")
    elif load_mode.lower() == 'append':
        key_cols = ["id"]  # Adjust if subitem_name exists
        cursor.execute(f"SELECT {', '.join(key_cols)} FROM [{table_name}]")
        existing_rows = set(tuple(str(cell) if cell is not None else '' for cell in row) for row in cursor.fetchall())
        df.fillna('', inplace=True)
        df = df[~df["id"].astype(str).isin([r[0] for r in existing_rows])]
        print(f"{len(df)} new rows to insert after filtering duplicates.")

    data_to_insert = [tuple(row.fillna('').values.tolist()) for _, row in df.iterrows()]
    if data_to_insert:
        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()

    cursor.close()
    conn.close()
    print(f"✅ Loaded {len(data_to_insert)} rows into {table_name} (Mode: {load_mode})")
    return len(data_to_insert)