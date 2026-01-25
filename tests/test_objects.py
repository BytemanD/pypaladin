from typing import Optional
# from sqlalchemy import Column, String

from peewee import CharField

from pypaladin_orm.objects import BaseObject
from pypaladin_orm.dbmodel import BaseDBModel




class UserDB(BaseDBModel):
    name = CharField(max_length=20)

    class Meta:  # type: ignore
        table_name = "users"


class User(BaseObject):
    __dbmodel__ = UserDB

    name: Optional[str] = ""


def test_user():
    User.delete_all()

    user1 = User(name="foo")
    user2 = User(name="bar")
    user1.create()
    user2.create()

    users = User.query()
    assert len(users) == 2
    assert users[0].name == "foo"
    assert users[1].name == "bar"

    user1.name = "zzz"
    user1.save()
    users = User.query()
    assert len(users) == 2
    assert users[0].name == "zzz"
    assert users[1].name == user2.name
