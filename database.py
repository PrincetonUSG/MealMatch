from datetime import datetime, date
from psycopg2 import connect
from os import environ
from big_lists import dhall_list


def new_connection():
    conn = connect(environ["DATABASE_URL"])
    cur = conn.cursor()
    return cur, conn


def close_connection(cur, conn):
    conn.commit()
    cur.close()
    conn.close()


def create_user_table():
    create_table_query = '''CREATE TABLE users
            (NETID TEXT PRIMARY KEY NOT NULL,
            NAME TEXT NOT NULL,
            YEAR INT NOT NULL,
            MAJOR TEXT NOT NULL,
            PHONENUM TEXT NOT NULL,
            BIO TEXT,
            MATCHPREF TEXT NOT NULL,
            RECUR BOOLEAN,
            RECUR_BEGINTIME TIMESTAMP,
            RECUR_ENDTIME TIMESTAMP,
            DAYS TEXT);'''

    cur, conn = new_connection()
    cur.execute(create_table_query)
    close_connection(cur, conn)


def create_matches_table():
    create_table_query = '''CREATE TABLE matches
            (MATCH_ID TEXT PRIMARY KEY NOT NULL,
            FIRST_NETID TEXT NOT NULL,
            SECOND_NETID TEXT NOT NULL,
            MATCH_TIME TIMESTAMP NOT NULL,
            DINING_HALL TEXT NOT NULL,
            START_WINDOW TIMESTAMP NOT NULL,
            END_WINDOW TIMESTAMP NOT NULL,
            FIRST_ACCEPTED BOOLEAN NOT NULL,
            SECOND_ACCEPTED BOOLEAN NOT NULL,
            ACTIVE BOOLEAN NOT NULL,
            LUNCH BOOLEAN NOT NULL);'''

    cur, conn = new_connection()
    cur.execute(create_table_query)
    close_connection(cur, conn)


def create_requests_table():
    create_table_query = '''CREATE TABLE requests
            (REQUESTID TEXT PRIMARY KEY NOT NULL,
            NETID TEXT NOT NULL,
            BEGINTIME TIMESTAMP NOT NULL,
            ENDTIME TIMESTAMP NOT NULL,
            LUNCH BOOLEAN NOT NULL,
            MATCHID TEXT,\n'''

    for i in dhall_list:
        create_table_query = create_table_query + \
            "{} BOOLEAN NOT NULL,\n".format(i)

    create_table_query = create_table_query + \
        "ATDHALL BOOLEAN, \n ACTIVE BOOLEAN NOT NULL);"

    cur, conn = new_connection()
    cur.execute(create_table_query)
    close_connection(cur, conn)


def create_metrics_table():
    create_table_query = ''' CREATE table metrics 
                            (DAY TEXT PRIMARY KEY NOT NULL, REQUESTS INT NOT NULL, MATCHES INT NOT NULL) '''

    cur, conn = new_connection()
    cur.execute(create_table_query)
    close_connection(cur, conn)


def create_new_day_usage_metrics():
    day_string = date.today().isoformat()
    init_metrics_query = ''' INSERT INTO metrics (day, requests, matches)
                            VALUES (\'{}\', 0, 0) '''.format(day_string)

    print('day string: ' + day_string)
    print('init metrics query ' + init_metrics_query)

    cur, conn = new_connection()
    cur.execute(init_metrics_query)
    close_connection(cur, conn)


def update_request_usage_metric():
    try:
        day_string = date.today().isoformat()
        increment_requests = ''' UPDATE metrics SET REQUESTS = REQUESTS + 1  WHERE day = \'{}\''''.format(
            day_string)
        cur, conn = new_connection()
        cur.execute(increment_requests)
        close_connection(cur, conn)
    except Exception as ex:
        print('EXCEPTION IN UPDATING MATCHES OCCURRED')
        print(ex)


def update_matches_usage_metric():
    try:
        day_string = date.today().isoformat()
        increment_requests = ''' UPDATE metrics SET MATCHES = MATCHES + 1  WHERE day = \'{}\''''.format(
            day_string)
        cur, conn = new_connection()
        cur.execute(increment_requests)
        close_connection(cur, conn)
    except Exception as ex:
        print('EXCEPTION IN UPDATING MATCHES OCCURRED')
        print(ex)


if __name__ == "__main__":
    clear_query = "DROP TABLE %s;"

    # cur, conn = new_connection()
    # for table in [
    #     # 'matches',
    #     # 'requests',
    #     # 'users',
    # ]:
    # cur.execute(clear_query, [table])
    # close_connection(cur, conn)
    # print('database deleted')

    # create_matches_table()
    # create_requests_table()
    # create_user_table()
    # create_metrics_table()
    print('database script ran')
