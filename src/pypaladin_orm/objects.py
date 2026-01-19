from typing import Any, Mapping, Optional, Set
from pydantic import BaseModel, PrivateAttr
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session

from pypaladin_orm.dbmodel import Base, BaseDBModel


class DBConfig(BaseModel):
    connection: str = "sqlite:///app.db"
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""


_DEFAULT_CONF: DBConfig = DBConfig()

_ENGINE: Optional[Engine] = None
_SESSION: Optional[sessionmaker] = None


def _engine():
    global _ENGINE
    if not _ENGINE:
        _ENGINE = create_engine(_DEFAULT_CONF.connection)
    return _ENGINE


_SESSION = sessionmaker(
    bind=_engine(), autocommit=False, autoflush=False, expire_on_commit=True
)


def _session() -> Session:
    global _SESSION

    if not _SESSION:
        _SESSION = sessionmaker(
            bind=_engine(), autocommit=False, autoflush=False, expire_on_commit=True
        )
    return _SESSION()


class BaseObject(BaseModel):
    __dbmodel__ = BaseDBModel
    _field_modified_: Set[str] = PrivateAttr(default_factory=set)

    id: Optional[int] = None

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self._field_modified_.add(name)

    @classmethod
    def query_all(cls):
        with _session() as session:
            query = session.query(cls.__dbmodel__)
        return [cls.model_validate(x, from_attributes=True) for x in query.all()]

    def _get_changes(self) -> Mapping[str, Any]:
        return {k: getattr(self, k) for k in self._field_modified_}

    def create(self):
        if self.id is not None:
            raise ValueError("Cannot create an existing object")

        db_model = self.__dbmodel__()
        for field in self.__class__.model_fields:
            if getattr(self, field) is None:
                continue
            setattr(db_model, field, getattr(self, field))

        with _session() as session:
            session.add(db_model)
            session.commit()
            session.refresh(db_model)
            self.id = db_model.id  # type: ignore
        self._field_modified_.clear()

    def save(self):
        changes = self._get_changes()
        if not changes:
            return
        if self.id is None:
            raise ValueError("Cannot save a new object")
        with _session() as session:
            session.query(self.__dbmodel__).filter_by(id=self.id).update(
                {k: v for k, v in changes.items()}
            )
            session.commit()
        self._field_modified_.clear()

    @classmethod
    def delete(cls, filters: dict = {}):
        with _session() as session:
            session.query(cls.__dbmodel__).filter_by(**filters).delete()
            session.commit()


def create_all():
    Base.metadata.create_all(_engine())
