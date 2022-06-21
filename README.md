# mysql-exp

Generates data migration scripts from MySQL

## Assumptions

This utility makes the following assumptions:

* The tables have a unique primary key of type `integer`.
* The table primary key column name value is managed by a sequence object.
* The sequence name is based on the primary key column name: for example,
  the table `user` has a PK column named `user_id` managed by a sequence named
  `user_id_seq`

## How it works

The utility generates a SQL script file with the commands to:
* Disable the existing table sequence association with the table primary key,
* Generate a `INSERT` command to copy table contents on new PgSql table.
* Re-enable the table sequence, starting at last PK id value, plus one.

## Examples

### Usage parameters

```commandline
python .\mysql-exp.py -h

usage: mysql-exp.py [-h] [-c CONFIG_FILE] -t TABLE_NAME [-o OUTPUT_FILE]

Creates a MySQL table data migration script. Currnetly, for PostgresSql

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Configuration file to be used by the migration flow.
  -t TABLE_NAME, --table-name TABLE_NAME
                        Source table name
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Source table name
```

### Generating a script

```commandline
python .\mysql-exp.py -t user -o user.sql
MySQL Data Exporter
Using the following parameters:

Host: localhost
Database: boxcar
TCP port 3306
User: boxcar
Table: role
Outcome file: role.sql
```

#### Outcome

```
-- Generated by MySQL data migration tool
-- Table: role
-- By: jfelixhe

DROP SEQUENCE IF EXISTS role_id_seq;
ALTER TABLE role ALTER COLUMN role_id DROP DEFAULT;

INSERT INTO role (role_id, role_name, role_description, row_creation_time, row_update_time, row_creation_user, row_update_user) VALUES
    (1, 'admin', 'Administrator', '2021-12-23 18:38:36', '2021-12-28 11:02:49', 'system', 'system')
    (2, 'logs', 'Allows application logs query', '2021-12-29 18:11:19', '2021-12-29 18:11:20', 'jfelixhe', 'jfelixhe')
    (3, 'operator', 'Admin console operator', '2021-12-29 18:12:27', '2021-12-29 18:12:27', 'jfelixhe', 'jfelixhe')
    (4, 'team-leader', 'Production team leader', '2022-03-23 16:30:52', '2022-03-23 16:30:52', 'dsergent', 'dsergent');

ALTER TABLE role ALTER COLUMN role_id SET DEFAULT NEXTVAL(('role_id_seq'::text)::REGCLASS);
CREATE SEQUENCE role_id_seq INCREMENT 1 START 5;
```
