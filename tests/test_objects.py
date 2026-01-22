from typing import Optional
from sqlalchemy import Column, String

from pypaladin_orm.objects import BaseObject, create_all
from pypaladin_orm.dbmodel import BaseDBModel

import fixture

class UserDB(BaseDBModel):
    __tablename__ = "users"

    name = Column(String(10))


class User(BaseObject):
    __dbmodel__ = UserDB

    name: Optional[str] = ""


def test_user():
    create_all()

    User.delete()

    user1 = User(name="foo")
    user2 = User(name="bar")
    user1.create()
    user2.create()

    users = User.query_all()
    print(users)

    user1.name = "zzz"
    user1.save()
    print(user1)
    users = User.query_all()
    print(users)
