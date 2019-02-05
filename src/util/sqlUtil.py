import mysql.connector


class SqlUtil(object):

    @staticmethod
    def connect():
        conn = mysql.connector.connect(
            host="mydb.itu.dk",
            user="fand_bsc_project",
            passwd="Bsc_2019",
            database="fand_bsc_project"
        )
        return conn

    @staticmethod
    def test_iteration_timing_insert_row(connection, row):
        mycursor = connection.cursor()
        sql = "INSERT INTO test_iteration_timing (time_begin, hostname, test_description, iterations, game_play_time) VALUES (%s, %s, %s, %s, %s)"

        # row = (time_begin, hostname, test_description, iterations, game_play_time)
    
        mycursor.execute(sql, row)
        connection.commit()

    @staticmethod
    def test_iteration_timing_insert_rows(connection, rows):
        mycursor = connection.cursor()
        sql = "INSERT INTO test_iteration_timing (time_begin, hostname, test_description, iterations, game_play_time) VALUES (%s, %s, %s, %s, %s)"
        
        # rows = [(time_begin, hostname, test_description, iterations, game_play_time),...]

        mycursor.executemany(sql, rows)
        connection.commit()