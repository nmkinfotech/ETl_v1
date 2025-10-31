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



def load_to_sql_monday_api(df:pd.DataFrame, table_name: str, connection_string: str, load_mode: str):
    connc_str = connection_string
    print("First Check Dataframe Type:",type(df))
    LOAD_MODE = load_mode
    conn= pyodbc.connect(connc_str)
    cursor = conn.cursor()

    cols = [col.replace('.', '_') for col in df.columns]  # replace dots for SQL

    print(df)

    columns_sql = ",\n".join([f"[{col}] {map_dtype(dtype)}" for col, dtype in df.dtypes.items()])

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

    if LOAD_MODE=='full':
        cursor.execute(f"DELETE FROM [{table_name}]")
        conn.commit()
        print(f"Table {table_name} truncated for full reload.")
    elif LOAD_MODE == 'append':
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}' AND COLUMN_NAME = 'subitem_name'
        """
        )

        has_subitems = cursor.fetchone() is not None

        if has_subitems:
            cursor.execute(f"""
                SELECT item_id, ISNULL(subitem_name) 
                FROM [{table_name}]
            """)
            existing_rows = set((str(row[0]),str(row[1]))  for row in cursor.fetchall())
            # print("First Check existing rows With Subitem:",existing_rows)
            print(f"{len(existing_rows)} existing (item_id + subitem_name) rows found in {table_name}.")
        else:
            cursor.execute(f"""SELECT item_id FROM {table_name}""")
            existing_rows = set(str(row[0]) for row in cursor.fetchall())
            # print("First Check existing rows Without Subitem:",existing_rows)
            print(f"{len(existing_rows)} existing item_id rows found in {table_name}")

        # Normalize DataFrame
        df.fillna('', inplace=True)
        
        # print("No manipulation till now in df\n")
        # print(df)
        # print("Second Check dataframe type :", type(df))

        if "subitem_name" in df.columns:
            df=df[~df.apply(lambda x:(str(x["item_id"]),str(x.get("subitem_name",""))) in existing_rows, axis=1)]
        else:
            df=df[~df["item_id"].astype(str).isin(existing_rows)]
        
        # print(f"{len(df)} new rows to insert.")
        print("Manipulation done\n")
        print(df)
        print(type(df))

    # Prepare data for bulk insert
    # print("Data Frame: \n", df )
    data_to_insert = [tuple(row.fillna('').values.tolist()) for _, row in df.iterrows()]

    # print(data_to_insert)

    if data_to_insert:
        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()

    cursor.close()
    conn.close()

    print(f"✅ Loaded {len(data_to_insert)} rows into {table_name} (Mode: {LOAD_MODE})")

    return len(data_to_insert)