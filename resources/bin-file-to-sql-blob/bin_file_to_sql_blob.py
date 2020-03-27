import pickle
from glob import glob
from util.sqlUtil import SqlUtil
from util.timerUtil import TimerUtil


def write_locale_file(game, filename="game30_sql_blob_test.bin"):
    try:
        new_file = open(filename, "xb")
        pickle.dump(game, new_file)
        new_file.close()
        print("game was saved to file")
    except IOError:
        print("something went wrong, when trying to save a replay")


def load_locale_file(filename="sql_blob_test.bin"):
    try:
        open_file = open(filename, "rb")
        game = pickle.load(open_file)
        open_file.close()
        print("Saved games were loaded from files")
        return game
    except IOError:
        print("something went wrong when trying to load games into buffer")


def sql_insert_blob(filename, game):
    pickeld_game = pickle.dumps(game)
    sql_conn = SqlUtil.connect()
    SqlUtil.game_data_insert_row(sql_conn, TimerUtil.get_computer_hostname(), filename, "sql blob testing",  pickeld_game)
    print("Game inserted into sql")

def sql_select_filename(filename):
    sql_conn = SqlUtil.connect()
    game = SqlUtil.game_data_select_filename(sql_conn, filename)
    unpickled_game = pickle.loads(game)
    print("Game selected from sql")
    return unpickled_game

load_filename="game30.bin"
game_file = load_locale_file(load_filename)     # Load from disk
sql_insert_blob(load_filename, game_file)       # Insert to SQL
game_sql = sql_select_filename(load_filename)   # Select from SQL
write_locale_file(game_sql, "game30_sql_blob.bin") # Write to disk