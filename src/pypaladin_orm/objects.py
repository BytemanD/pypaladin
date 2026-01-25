from typing import Any, Literal, Mapping, Optional, Sequence, Set, Type

from loguru import logger
from peewee import ModelSelect, SqliteDatabase, MySQLDatabase, PostgresqlDatabase
from pydantic import BaseModel, Field, PrivateAttr

from pypaladin_orm.dbmodel import BaseDBModel, db_proxy, _tables


class DBConfig(BaseModel):
    driver: Literal["sqlite", "mysql", "postgress"] = "sqlite"
    database: str = Field(default=":memory:", min_length=1)
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""

    authcommit: bool = True
    auto_create_tables: bool = False


class BaseObject(BaseModel):
    __dbmodel__ = BaseDBModel
    _field_modified_: Set[str] = PrivateAttr(default_factory=set)

    id: Optional[int] = None

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self._field_modified_.add(name)

    @classmethod
    def query(
        cls,
        filters: Optional[Mapping[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        query: ModelSelect = cls.__dbmodel__.select()

        if filters:
            conditions = None
            for k, v in filters.items():
                condition = getattr(cls.__dbmodel__, k) == v
                if conditions is None:
                    conditions = condition
                else:
                    conditions &= condition
            query = query.where(conditions)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return [cls.model_validate(x, from_attributes=True) for x in query]

    def _get_changes(self) -> Mapping[str, Any]:
        return {k: getattr(self, k) for k in self._field_modified_}

    def create(self):
        if self.id is not None:
            raise ValueError("Cannot create an existing object")

        db_model = self.__dbmodel__.create(**self.model_dump(exclude_none=True))
        self.id = db_model.id
        self._field_modified_.clear()

    def save(self):
        if self.id is None:
            raise ValueError("Cannot save a new object")
        changes = self._get_changes()
        if not changes:
            return
        self.__dbmodel__.update(**changes).where(
            getattr(self.__dbmodel__, "id") == self.id
        ).execute()
        self._field_modified_.clear()

    def delete(self):
        if self.id is None:
            raise ValueError("Cannot delete a new object")

        self.__dbmodel__.delete().where(
            getattr(self.__dbmodel__, "id") == self.id
        ).execute()

    @classmethod
    def delete_by_values(cls, **filters):
        if not filters:
            raise ValueError("No filters provided")
        conditions = None
        for k, v in filters.items():
            condition = getattr(cls.__dbmodel__, k) == v
            if conditions is None:
                conditions = condition
            else:
                conditions &= condition

        cls.__dbmodel__.delete().where(conditions)

    @classmethod
    def delete_all(cls):
        """删除所有数据"""
        cls.__dbmodel__.delete().execute()


def _create_db(dbconf: DBConfig):
    if dbconf.driver == "sqlite":
        return SqliteDatabase(
            dbconf.database,
            pragmas={
                # "cache_size": -1024 * 64,  # 64MB 缓存
                # "foreign_keys": 1,  # 启用外键约束
                "ignore_check_constraints": 0,
            },
            check_same_thread=False,  # 关键参数：允许不同线程使用同一个连接
        )
    elif dbconf.driver == "mysql":
        return MySQLDatabase(
            dbconf.database,
            host=dbconf.host,
            port=dbconf.port,
            user=dbconf.user,
            password=dbconf.password,
        )
    elif dbconf.driver == "postgress":
        return PostgresqlDatabase(
            dbconf.database,
            host=dbconf.host,
            port=dbconf.port,
            autoconnect=dbconf.authcommit,
        )
    raise ValueError(f"Invalid database driver: {dbconf.driver}")


def setup_db(dbconf: DBConfig):
    db = _create_db(dbconf)
    db.connect()

    db_proxy.initialize(_create_db(dbconf))
    if dbconf.auto_create_tables and _tables:
        logger.trace("create tables")
        db.create_tables(_tables)
