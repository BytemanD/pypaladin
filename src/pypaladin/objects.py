from typing import (
    Any,
    ClassVar,
    Mapping,
    Optional,
    Set,
    Type,
)
from pydantic import BaseModel, PrivateAttr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pypaladin.orm import BaseDBModel


engine = create_engine("sqlite:///xxx.db")
Session = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=True
)


class BaseObject(BaseModel):
    __dbmodel__ = BaseDBModel
    _dbmodel_: ClassVar[Type[BaseDBModel]] = BaseDBModel

    __modified: Set[str] = PrivateAttr(default_factory=set)

    id: Optional[int] = None

    @classmethod
    def query_all(cls):
        with Session() as session:
            query = session.query(cls.__dbmodel__)
        return [cls.model_validate(x, from_attributes=True) for x in query.all()]

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.__modified.add(name)

    def _get_changes(self) -> Mapping[str, Any]:
        return {k: getattr(self, k) for k in self.__modified}

    def create(self):
        if self.id is not None:
            raise ValueError("Cannot create an existing object")

        db_model = self.__dbmodel__()
        for field in self.__class__.model_fields:
            if getattr(self, field) is None:
                continue
            setattr(db_model, field, getattr(self, field))

        with Session() as session:
            session.add(db_model)
            session.commit()
            session.refresh(db_model)
            self.id = db_model.id # type: ignore
        self.__modified.clear()

    def save(self):
        changes = self._get_changes()
        if not changes:
            return
        if self.id is None:
            raise ValueError("Cannot save a new object")
        with Session() as session:
            session.query(self.__dbmodel__).filter_by(id=self.id).update(
                {k: v for k, v in changes.items()}
            )
            session.commit()
        self.__modified.clear()

    @classmethod
    def delete(cls, filters: dict = {}):
        with Session() as session:
            session.query(cls.__dbmodel__).filter_by(**filters).delete()
            session.commit()
