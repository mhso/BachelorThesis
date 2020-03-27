import mysql.connector
import datetime
from config import Config

class SqlUtil(object):
    training_id = 0
    connection = None

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
    def execute_query(query, connection, data=None, result=False):
        try:
            cursor = connection.cursor()
            cursor.execute(query, data)
            query_result = None
            if result == "id":
                query_result = cursor.lastrowid
            elif result == "select":
                query_result = cursor.fetchone()
            connection.commit()
            return query_result
        except IOError:
            print("ERROR IN MYSQL THINGS")
            return None

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

    @staticmethod
    def evaluation_cost_row(time_begin, hostname, pid, test_name, test_description, rand_seed_used, player_white, player_black, moves_white, moves_black, pieces_white, pieces_black, game_duration):
        return (time_begin, hostname, pid, test_name, test_description, rand_seed_used, player_white, player_black, moves_white, moves_black, pieces_white, pieces_black, game_duration)

    @staticmethod
    def evaluation_cost_insert_row(connection, row):
        mycursor = connection.cursor()
        sql = "INSERT INTO evaluation_cost (time_begin, hostname, pid, test_name, test_description, rand_seed_used, player_white, player_black, moves_white, moves_black, pieces_white, pieces_black, game_duration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        # row = (time_begin, hostname, pid, test_name, test_description, rand_seed_used, player_white, player_black, moves_white, moves_black, pieces_white, pieces_black, game_duration)
    
        mycursor.execute(sql, row)
        connection.commit()

    @staticmethod
    def game_data_insert_row(connection, hostname, filename, description, bin_data):
        mycursor = connection.cursor()
        sql = "INSERT INTO game_data (hostname, filename, description, bin_data) VALUES (%s, %s, %s, %s)"
        row = (hostname, filename, description, bin_data)
    
        mycursor.execute(sql, row)
        connection.commit()

    
    @staticmethod
    def game_data_select_newest_games(connection):
        mycursor = connection.cursor()
        sql = "SELECT bin_data FROM game_data ORDER BY id DESC LIMIT {}".format(Config.MAX_GAME_STORAGE)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        return result


    @staticmethod
    def network_data_insert_row(connection, hostname, filename, description, bin_data):
        mycursor = connection.cursor()
        sql = "INSERT INTO network_data (hostname, filename, description, bin_data) VALUES (%s, %s, %s, %s)"
        row = (hostname, filename, description, bin_data)
    
        mycursor.execute(sql, row)
        connection.commit()
        print("done with network data commit")


    @staticmethod
    def network_data_select_newest_network(connection):
        mycursor = connection.cursor()
        sql = "SELECT bin_data FROM network_data ORDER BY id DESC LIMIT 1"
        mycursor.execute(sql)
        result = mycursor.fetchone()
        return result


    @staticmethod
    def eval_data_insert_row(connection, hostname, filename, description, bin_data):
        mycursor = connection.cursor()
        sql = "INSERT INTO eval_data (hostname, filename, description, bin_data) VALUES (%s, %s, %s, %s)"
        row = (hostname, filename, description, bin_data)
    
        mycursor.execute(sql, row)
        connection.commit()
        print("done with eval data commit")


    
    @staticmethod
    def game_data_select_filename(connection, file_name):
        mycursor = connection.cursor()
        sql = "SELECT * FROM game_data WHERE filename='{}'".format(file_name)
        mycursor.execute(sql)
        result = mycursor.fetchone()

        db_id = result[0]
        created = result[1]
        hostname = result[2]
        filename = result[3]
        description = result[4]
        bin_data = result[5]

        return bin_data

    @staticmethod
    def add_status(connection):
        date = datetime.datetime.now()
        formatted_date = date.strftime('%Y-%m-%d %H:%M:%S')
        sql = ("INSERT INTO training_status (active, step, total_steps, loss, games, eval_rand, eval_mini, eval_mcts, time_started)"+
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
        row = (1, 0, 0, 0, 0, 0, 0, 0, formatted_date)

        SqlUtil.training_id = SqlUtil.execute_query(sql, connection, row, "id")

    @staticmethod
    def get_latest_status(connection):
        sql = "SELECT id FROM training_status ORDER BY id DESC LIMIT 1"

        SqlUtil.training_id = SqlUtil.execute_query(sql, connection, "select")[0]

    @staticmethod
    def set_status(connection, var_string, data=None):
        sql = f"UPDATE training_status SET {var_string} WHERE id=%s"
        row = (SqlUtil.training_id,) if data is None else (data, SqlUtil.training_id)

        SqlUtil.execute_query(sql, connection, row)
