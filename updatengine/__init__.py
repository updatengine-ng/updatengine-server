#
# Uncomment lines below in case of error "Did you install mysqlclient or MySQL-python ?" :
# and run ${INST_DIR}/bin/pip3 install pymysql
#
'''
import pymysql

pymysql.version_info = (1, 3, 13, "final", 0)
pymysql.install_as_MySQLdb()
'''
