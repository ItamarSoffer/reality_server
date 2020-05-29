import sqlite3
import pandas as pd

# ##############################################
# #########        DB FUNCTIONS        #########
# ##############################################


# change to context manager.
def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def run(db_file, query, keep_open=False):
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query)
    except Exception as e:
        print(e)
    finally:
        if not keep_open:
            connection.close()


def insert(db_file, table, columns, data, keep_open=False):
    insertion_query = """ 
    INSERT INTO {table_name}({columns})
    VALUES({data})
    """
    lined_columns = ",".join([str(val) for val in columns])
    lined_data = ",".join(["?" for val in columns])
    query = insertion_query.format(
        table_name=table, columns=lined_columns, data=lined_data
    )
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query, data)
        connection.commit()
    except Exception as e:
        print(f"Tried to run:\n {query}")
        print(f"Error: {e}")
    finally:
        if not keep_open:
            connection.close()


# maybe change to 2 functions: one returns data and and headers and one changes to dicts.
# change to context_manager
def query_to_json(db_file, query_string, args=[], keep_open=False):
    """
    query the data from the db.
    returns a list of dicts- each result is a json.
    :param db_file:
    :param query_string:
    :param args:
    :param keep_open: dont close the connection to db.
    :return:
    """
    results = None
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query_string, args)
        headers = [description[0] for description in c.description]
        raw_results = c.fetchall()
        results = []
        for record in raw_results:
            dict_record = {}
            for i in range(len(headers)):
                dict_record[headers[i]] = record[i]
            results.append(dict_record)
    except Exception as e:
        print(e)
    finally:
        if not keep_open:
            connection.close()
    return results


def query_to_df(db_file, query_string, args=[], keep_open=False):
    """
    Queries the db and returns the results as dataframe
    :param db_file:
    :param query_string:
    :param args:
    :param keep_open:
    :return:
    """
    if type(args) == str:
        args = [args]
    table_results = None
    connection = create_connection(db_file)
    try:
        c = connection.cursor()
        c.execute(query_string, args)
        headers = [description[0] for description in c.description]
        raw_results = c.fetchall()
        table_results = pd.DataFrame(columns=headers, data=raw_results)
    except Exception as e:
        print(e)
    finally:
        if not keep_open:
            connection.close()
    return table_results

