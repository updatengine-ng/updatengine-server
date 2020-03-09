# -*- coding: utf-8 -*-

## Convert all updatengine tables to utf8
# ~ INST_DIR=/var/www/UE-environment
# ~ cd ${INST_DIR}/updatengine-server
# ~ ../bin/python manage.py runscript db_convert_utf8
# ~ OR:
# ~ ${INST_DIR}/bin/python ${INST_DIR}/updatengine-server/manage.py runscript db_convert_utf8

from django.db import connection

def run():
    cursor = connection.cursor()
    tables = connection.introspection.table_names(cursor)

    for table in tables:
        print("Fixing table: %s" %table)
        sql = "ALTER TABLE %s CONVERT TO CHARACTER SET utf8mb4;" %(table)
        cursor.execute(sql)
        print("Table %s set to utf8mb4"%table)

    print("DONE!")
