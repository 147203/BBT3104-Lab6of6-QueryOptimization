"""
Purpose: Log the actual number of rows returned by SELECT queries in the IMDb
         database. This is needed to create the training and testing dataset
         stored in the query_log table.
"""
import psycopg2
from datetime import datetime
import yaml
from ruamel.yaml import YAML

# Create the following table in the IMDb database first:
# CREATE TABLE query_log (
#     id SERIAL PRIMARY KEY,
#     query_text TEXT,
#     actual_rows INTEGER,
#     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );

def connect_to_database(conn_params):
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

def set_schema(conn, schema):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {schema};")
        conn.commit()
    except Exception as e:
        print(f"Error setting schema: {e}")
    finally:
        if cursor:
            cursor.close()

def read_queries_from_file(file_path):
    with open(file_path, 'r') as file:
        # Assumption: Each query is separated by a semicolon
        queries = file.read().strip().split(';')
    # Removes any empty strings that may result from splitting
    queries = [query.strip() for query in queries if query.strip()]
    # TODO: Remove any comments from the queries
    return queries

def execute_queries(conn, query):
    cursor = None
    try:
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error executing queries from file: {e}")
    
    # Get the EXPLAIN ANALYZE output in YAML format
    cursor.execute("EXPLAIN (BUFFERS, VERBOSE, ANALYZE, FORMAT YAML) " + query)
    analyze_results = cursor.fetchall()
    analyze_data = yaml.safe_load(analyze_results[0][0])

    # Get the EXPLAIN output in YAML format (not mandatory)
    cursor.execute("EXPLAIN (FORMAT YAML) " + query)
    explain_results = cursor.fetchall()
    explain_data = yaml.safe_load(explain_results[0][0])

    # Process YAML data to extract actual and estimated rows and maintain node order
    def extract_rows(data, key_actual, key_estimated):
        q_error_results = []

        def recurse_nodes(node, path=""):
            node_type = node.get('Node Type', 'Unknown')
            new_path = f"{path}/{node_type}" if path else node_type
            if 'Plans' in node:
                for subnode in node['Plans']:
                    recurse_nodes(subnode, new_path)

            actual_rows = node.get(key_actual, 0)
            estimated_rows = node.get(key_estimated, 0)
            if actual_rows > 0:
                q_error = max(estimated_rows / actual_rows, actual_rows / estimated_rows)
            else:
                q_error = float('inf')  # Handle cases where actual rows are zero
            q_error_results.append((new_path, actual_rows, estimated_rows, q_error))

        recurse_nodes(data[0]['Plan'])
        return q_error_results

    actual_key = 'Actual Rows'
    estimated_key = 'Plan Rows'
    q_error = extract_rows(analyze_data, actual_key, estimated_key)

    return q_error

def log_queries(conn, query, actual_rows):
    cursor = None
    try:
        cursor = conn.cursor()
        try:
            if actual_rows is not None:
                cursor.execute("""
                    INSERT INTO query_log (query_text, actual_rows, timestamp) 
                    VALUES (%s, %s, %s);
                """, (query, actual_rows, datetime.now()))
                
                print(f"\nLOGGED QUERY:\n"
                        f"INSERT INTO query_log (query_text, actual_rows, timestamp) "
                        f"VALUES ({query}, {actual_rows}, {datetime.now()})")
            else:
                print(f"Could not determine actual rows for query: {query}")
        except Exception as e:
            print(f"Error logging query: {query}\nError: {e}")
        
        conn.commit()
    except Exception as e:
        print(f"Error logging SELECT statements: {e}")
    finally:
        if cursor:
            cursor.close()

def main():
    # Database connection parameters
    conn_params = {
        'database': 'imdb',
        'user': 'postgres',
        'password': '5trathm0re',
        'host': 'localhost',
        'port': '5432'
    }

    # Connect to the PostgreSQL database
    conn = connect_to_database(conn_params)
    if not conn:
        return

    try:
        # Set the schema
        set_schema(conn, 'imdb_schema')

        # Execute queries from file
        file_path = 'Join-Order-Benchmark-queries/JOB-light-3.sql'
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        queries = read_queries_from_file(file_path)
        for query in queries:
            q_error = execute_queries(conn, query)
            print("\n\n--------------------------------------------------")
            print("\nQuery Execution Plan (QEP):")
            for node, actual, estimated, error in q_error:
                print(f"Node: {node}, Actual Rows: {actual}, Estimated Rows: {estimated}, Q-Error: {error}")
            print("\n")
            print("QUERY:\n", query)
            print("\n")
            print("ACTUAL ROWS:\n", actual)
            log_queries(conn, query, actual)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
