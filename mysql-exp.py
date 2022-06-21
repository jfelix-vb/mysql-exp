#  File name: mysql-exp.py
#
#  Project: mysql-exp
#  Creates external database data migration script.
#
#  Created by: jfelix@vonbraunlabs.com.br
#  Date: 2022-06-18, 10:53 AM
#
#  Copyright Von Braun Labs. 2022.

import argparse
import configparser

import pymysql

config_file_contents = configparser.ConfigParser()


def get_table_primary_key(table_descriptor):
    return [column for column in table_descriptor if column[3] == 'PRI'][0]


def get_table_primary_key_index(table_descriptor) -> int:
    for i, column in enumerate(table_descriptor):
        if column[3] == 'PRI':
            return i

    return 0


def append_initial_comments(table_name: str, outcome_text: []):
    outcome_text.append("-- Generated by MySQL data migration tool")
    outcome_text.append("-- Table: {}".format(table_name))
    outcome_text.append("-- By: jfelixhe")
    outcome_text.append("")


def append_sequence_disabling(table_name: str, primary_key_descriptor: [], outcome_text: []):
    outcome_text.append("DROP SEQUENCE IF EXISTS {0}_seq;".format(primary_key_descriptor[0]))
    outcome_text.append("ALTER TABLE {0} ALTER COLUMN {1} DROP DEFAULT;".format(table_name, primary_key_descriptor[0]))
    outcome_text.append("")


def append_sequence_enabling(table_name: str, primary_key_descriptor: [], outcome_text: [], max_primary_key_id: int):
    outcome_text.append("")
    outcome_text.append("ALTER TABLE {0} ALTER COLUMN {1} SET DEFAULT NEXTVAL(('{1}_seq'::text)::REGCLASS);"
                        .format(table_name, primary_key_descriptor[0]))
    outcome_text.append("CREATE SEQUENCE {0}_seq INCREMENT 1 START {1};"
                        .format(primary_key_descriptor[0], max_primary_key_id + 1))


def comma_separated_columns(table_descriptor: []) -> str:

    table_column_names = [column[0] for column in table_descriptor]
    return ", ".join(table_column_names)


def append_data_insert(table_name: str, table_descriptor: [], primary_key_index: int,
                       mysql_connection: pymysql.Connection, outcome_text: []) -> int:
    table_data_cursor = mysql_connection.cursor()
    table_data_cursor.execute("SELECT * FROM " + table_name)

    table_data = table_data_cursor.fetchall()

    # print(table_data)

    outcome_text.append("INSERT INTO {0} ({1}) VALUES".format(table_name, comma_separated_columns(table_descriptor)))

    max_primary_key_id = 0
    for data_row in table_data:
        outcome_text.append("    ({0})".format(generate_data_row_text(data_row, table_descriptor)))
        max_primary_key_id = data_row[primary_key_index]

    return max_primary_key_id


def generate_data_row_text(data_row: [], table_descriptor: []) -> str:

    data_tokens = []

    for i, data_token in enumerate(data_row):
        data_tokens.append(get_data_token_representation(data_token, table_descriptor[i][1]))

    return ", ".join(data_tokens)


def get_data_token_representation(data_token, data_type: str) -> str:
    if 'int' in data_type:
        return str(data_token)
    elif 'varchar' in data_type:
        return '\'' + data_token + '\''
    elif 'datetime' in data_type:
        return '\'' + data_token.strftime('%Y-%m-%d %H:%M:%S') + '\''
    elif 'bool' in data_type:
        return data_token
    elif data_type == 'bit(1)':
        return 'True' if data_token == 1 else 'False'
    else:
        return "''"


def create_data_export_script(host: str, database: str, port: int, user: str, password: str, table_name: str,
                              output_file: str):

    mysql_connection = pymysql.connect(host=host,
                                       database=database,
                                       port=port,
                                       user=user,
                                       password=password,
                                       ssl={"fake_flag_to_enable_tls": True})

    outcome_text = []

    try:
        table_metadata_cursor = mysql_connection.cursor()
        table_metadata_cursor.execute("DESCRIBE " + table_name)

        table_descriptor = table_metadata_cursor.fetchall()

        primary_key_column = get_table_primary_key(table_descriptor)
        primary_key_index = get_table_primary_key_index(table_descriptor)

        append_initial_comments(table_name, outcome_text)
        append_sequence_disabling(table_name, primary_key_column, outcome_text)
        max_primary_key_id = append_data_insert(
            table_name, table_descriptor, primary_key_index, mysql_connection, outcome_text)
        append_sequence_enabling(table_name, primary_key_column, outcome_text, max_primary_key_id)

        # print(outcome_text)
        with open(output_file, 'w') as file:
            for text_line in outcome_text:
                file.write("%s\n" % text_line)

    except Exception as e:
        print("Exception occured: {}".format(e))
        exit(-1)

    finally:
        mysql_connection.close()


# Application entry point.
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Creates a MySQL table data migration script. Currnetly, for PostgresSql ')

    parser.add_argument('-c', '--config-file', type=str, default='mysql-exp.conf',
                        help='Configuration file to be used by the migration flow.')

    parser.add_argument('-t', '--table-name', type=str, required=True,
                        help='Source table name')

    parser.add_argument('-o', '--output-file', type=str, default='output.sql',
                        help='Source table name')

    args = vars(parser.parse_args())
    config_file_contents.read(args['config_file'])

    print('MySQL Data Exporter\nUsing the following parameters:\n')
    print('Host: ' + config_file_contents['source']['host'])
    print('Database: ' + config_file_contents['source']['database'])
    print('TCP port ' + config_file_contents['source']['port'])
    print('User: ' + config_file_contents['source']['user'])
    print('Table: ' + args['table_name'])
    print('Outcome file: ' + args['output_file'])
    print()

    create_data_export_script(
        config_file_contents['source']['host'],
        config_file_contents['source']['database'],
        int(config_file_contents['source']['port']),
        config_file_contents['source']['user'],
        config_file_contents['source']['password'],
        args['table_name'],
        args['output_file']
    )
