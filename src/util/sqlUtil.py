import mysql.connector
import constants


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
        sql = "SELECT filename FROM game_data ORDER BY id DESC LIMIT {}".format(constants.MAX_GAME_STORAGE)
        print(sql)
        mycursor.execute(sql)
        result = mycursor.fetchall()
        print(result)
        return result

    
    @staticmethod
    def game_data_select_filename(connection, file_name):
        mycursor = connection.cursor()
        sql = "SELECT * FROM game_data WHERE filename='{}'".format(file_name)
        print(sql)
        mycursor.execute(sql)
        result = mycursor.fetchone()

        db_id = result[0]
        created = result[1]
        hostname = result[2]
        filename = result[3]
        description = result[4]
        bin_data = result[5]

        return bin_data