from peewee import Model, AutoField, DatabaseProxy

db_proxy = DatabaseProxy()

_tables = []


class BaseDBModel(Model):
    id = AutoField()

    class Meta:
        database = db_proxy

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls not in _tables:
            _tables.append(cls)
