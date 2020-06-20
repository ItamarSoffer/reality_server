import sqlite3
import pandas as pd


class Database(object):
    def __init__(self, db_file):
        self.db_file = db_file

    # change to context manager.
    def _create_connection(self):
        """ create a database connection to the SQLite database
            specified by db_file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except Exception as e:
            print(e)

        return conn

    def run(self, query, args=[], keep_open=False):
        if type(args) == str:
            args = [args]
        connection = self._create_connection()
        try:
            c = connection.cursor()
            c.execute(query, args)
            connection.commit()
        except Exception as e:
            print(e)
        finally:
            if not keep_open:
                connection.close()

    def insert(self, table, columns, data, keep_open=False):
        insertion_query = """ 
        INSERT INTO {table_name}({columns})
        VALUES({data})
        """
        lined_columns = ",".join([str(val) for val in columns])
        lined_data = ",".join(["?" for val in columns])
        query = insertion_query.format(
            table_name=table, columns=lined_columns, data=lined_data
        )
        connection = self._create_connection()
        try:
            c = connection.cursor()
            c.execute(query, data)
            connection.commit()
        except Exception as e:
            print("Tried to run:\n {query}".format(query=query))
            print("Error: {e}".format(e=e))
        finally:
            if not keep_open:
                connection.close()

    # maybe change to 2 functions: one returns data and and headers and one changes to dicts.
    # change to context_manager
    def query_to_json(self, query_string, args=[], keep_open=False):
        """
        query the data from the db.
        returns a list of dicts- each result is a json.
        :param db_file:
        :param query_string:
        :param args:
        :param keep_open: dont close the connection to db.
        :return:
        """
        headers, raw_results = self.query(query_string, args, keep_open)
        results = []
        for record in raw_results:
            dict_record = {}
            for i in range(len(headers)):
                dict_record[headers[i]] = record[i]
            results.append(dict_record)
        return results

    def query_to_df(self, query_string, args=[], keep_open=False):
        """
        Queries the db and returns the results as dataframe
        :param query_string:
        :param args:
        :param keep_open:
        :return:
        """
        headers, raw_results = self.query(query_string, args, keep_open)
        return pd.DataFrame(columns=headers, data=raw_results)

    def query(self, query_string, args=[], keep_open=False, return_headers=True):
        """
        Queries the db and returns the results as dataframe
        :param query_string:
        :param args:
        :param keep_open:
        :return:
        """
        headers, raw_results = [], []
        if type(args) == str:
            args = [args]
        connection = self._create_connection()
        try:
            c = connection.cursor()
            c.execute(query_string, args)
            headers = [description[0] for description in c.description]
            raw_results = c.fetchall()
        except Exception as e:
            print(e)
        finally:
            if not keep_open:
                connection.close()
        if return_headers:
            return headers, raw_results
        else:
            return raw_results


