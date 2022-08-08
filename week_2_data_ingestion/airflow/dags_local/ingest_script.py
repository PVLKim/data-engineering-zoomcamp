import os

from time import time

import pandas as pd
from pyarrow.parquet import ParquetFile
import pyarrow as pa 
from sqlalchemy import create_engine


def ingest_callable(user, password, host, port, db, table_name, csv_file, execution_date):
    print(table_name, csv_file, execution_date)
    print(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    engine.connect()

    print('connection established successfully, inserting data...')

    t_start = time()
    # df_iter = pd.read_csv(csv_file, iterator=True, chunksize=100000)
    pf = ParquetFile(csv_file) 
    pf_iter = pf.iter_batches(batch_size = 100000) 
    df = pa.Table.from_batches([next(pf_iter)]).to_pandas()
    # df = next(df_iter)

    # df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    # df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='append')

    df.to_sql(name=table_name, con=engine, if_exists='append')

    t_end = time()
    print('inserted the first chunk, took %.3f second' % (t_end - t_start))

    while True: 
        t_start = time()

        try:
            df = pa.Table.from_batches([next(pf_iter)]).to_pandas()
            # df = next(df_iter)
        except StopIteration:
            print("completed")
            break

        # df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        # df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

        df.to_sql(name=table_name, con=engine, if_exists='append')

        t_end = time()

        print('inserted another chunk, took %.3f second' % (t_end - t_start))
