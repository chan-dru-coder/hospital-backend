import pymysql

# Install PyMySQL as MySQLdb first
pymysql.install_as_MySQLdb()

# Now patch MySQL version check to support MySQL 8.0 with Django 5.1+
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None
