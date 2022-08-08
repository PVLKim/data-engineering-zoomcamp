import os
from datetime import datetime

from airflow import DAG

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from ingest_script import ingest_callable


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
PG_HOST = os.getenv('PG_HOST')
PG_USER = os.getenv('PG_USER')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_PORT = os.getenv('PG_PORT')
PG_DATABASE = os.getenv('PG_DATABASE')

default_args = {
    "owner": "airflow",
    #"start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

def download_ingest_dag(
    dag,
    url_template,
    local_parquet_path_template, 
    table_name
):
    with dag:

        download_dataset_task = BashOperator(
            task_id="download_dataset_task",
            bash_command=f'wget {url_template} -O {local_parquet_path_template}'
        )

        local_to_psql_task = PythonOperator(
            task_id="local_to_psql_task",
            python_callable=ingest_callable,
            op_kwargs=dict(
                user=PG_USER,
                password=PG_PASSWORD,
                host=PG_HOST,
                port=PG_PORT,
                db=PG_DATABASE,
                table_name=table_name,
                csv_file=local_parquet_path_template
            )
        )

        rm_task = BashOperator(
            task_id="rm_task",
            bash_command=f"rm {local_parquet_path_template}"
        )

        download_dataset_task >> local_to_psql_task >> rm_task


URL_PREFIX = 'http://192.168.1.83:8000/' 

# URL_PREFIX = 'https://d37ci6vzurychx.cloudfront.net/trip-data' 
YELLOW_TAXI_URL_TEMPLATE = URL_PREFIX + '/yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.parquet'
YELLOW_TAXI_PARQUET_FILE_TEMPLATE = AIRFLOW_HOME + '/yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.parquet'
YELLOW_TAXI_TABLE_NAME = 'yellow_tripdata'

yellow_taxi_data_dag = DAG(
    dag_id="yellow_taxi_data_v2",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2022, 1, 1),
    end_date=datetime(2022, 3, 1),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de'],
)

download_ingest_dag(
    dag=yellow_taxi_data_dag,
    url_template=YELLOW_TAXI_URL_TEMPLATE,
    local_parquet_path_template=YELLOW_TAXI_PARQUET_FILE_TEMPLATE,
    table_name=YELLOW_TAXI_TABLE_NAME
)


GREEN_TAXI_URL_TEMPLATE = URL_PREFIX + '/green_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.parquet'
GREEN_TAXI_PARQUET_FILE_TEMPLATE = AIRFLOW_HOME + '/green_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.parquet'
GREEN_TAXI_TABLE_NAME = 'green_tripdata'

green_taxi_data_dag = DAG(
    dag_id="green_taxi_data_v1",
    schedule_interval="0 7 2 * *",
    start_date=datetime(2022, 1, 1),
    end_date=datetime(2022, 3, 1),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de'],
)

download_ingest_dag(
    dag=green_taxi_data_dag,
    url_template=GREEN_TAXI_URL_TEMPLATE,
    local_parquet_path_template=GREEN_TAXI_PARQUET_FILE_TEMPLATE,
    table_name=GREEN_TAXI_TABLE_NAME
)
