import os

import duckdb


def check_parquet_file(package_name):
    parquet_file = f"maven-stats-source/accumulation/{package_name}.parquet"

    # Check if the file exists
    if not os.path.exists(parquet_file):
        print(f"Parquet file for {package_name} does not exist.")
        return

    # Connect to DuckDB in-memory and load the Parquet file
    conn = duckdb.connect(database=":memory:")

    # Load the parquet file into a DuckDB table
    try:
        result = conn.sql(
            f"SELECT * FROM read_parquet('{parquet_file}') ORDER BY year_month"
        ).fetch_df()
        print(result)
    except Exception as e:
        print(f"Error while reading the Parquet file: {e}")


# Replace 'your_package_name' with the actual package name you want to check
package_name = "cdk-comprehend-s3olap"
check_parquet_file(package_name)
