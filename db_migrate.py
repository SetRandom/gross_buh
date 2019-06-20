__version__ = '0.1'
from playhouse.migrate import *

from app import database


def migrate_me():
    migrator = PostgresqlMigrator(database)

    migrate(
        migrator.add_column('checkstring', 'error', TextField(null=True, default=None))
    )


if __name__ == '__main__':
    try:
        migrate_me()
    except:
        print('No migrate')
