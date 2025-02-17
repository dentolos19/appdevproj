import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from lib.enums import TransactionType


class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    name: Mapped[str]
    points: Mapped[int] = mapped_column(default=0)
    bio: Mapped[Optional[str]]
    birthday: Mapped[Optional[str]]  # TODO: Use datetime
    security: Mapped[Optional[str]]

    followings: Mapped[List["UserFollow"]] = relationship(back_populates="user", foreign_keys="UserFollow.user_id")
    followers: Mapped[List["UserFollow"]] = relationship(
        back_populates="follower", foreign_keys="UserFollow.follower_id"
    )


class UserFollow(Base):
    __tablename__ = "user_follows"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    follower_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    user = relationship("User", foreign_keys=[user_id], back_populates="followings")
    follower = relationship("User", foreign_keys=[follower_id], back_populates="followers")


class Event(Base):
    __tablename__ = "events"

    title: Mapped[str]
    description: Mapped[Optional[str]]
    location: Mapped[str]
    date: Mapped[str]
    image_url: Mapped[Optional[str]]

    attendees: Mapped[List["EventAttendee"]] = relationship(back_populates="event", cascade="all, delete")


class EventAttendee(Base):
    __tablename__ = "event_attendees"

    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    event: Mapped["Event"] = relationship(back_populates="attendees")
    user: Mapped["User"] = relationship()


class Post(Base):
    __tablename__ = "posts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str]
    image_url: Mapped[Optional[str]]

    user: Mapped["User"] = relationship()
    likes: Mapped[List["PostLike"]] = relationship(back_populates="post", cascade="all, delete")
    messages: Mapped[List["PostComment"]] = relationship(back_populates="post", cascade="all, delete")
    saves: Mapped[List["PostSaved"]] = relationship(back_populates="post", cascade="all, delete")


class PostLike(Base):
    __tablename__ = "post_likes"

    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    post: Mapped["Post"] = relationship(back_populates="likes")
    user: Mapped["User"] = relationship()


class PostComment(Base):
    __tablename__ = "post_comments"

    message: Mapped[str]

    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    post: Mapped["Post"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship()


class PostSaved(Base):
    __tablename__ = "post_save"

    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    post: Mapped["Post"] = relationship(back_populates="saves")
    user: Mapped["User"] = relationship()


class Task(Base):
    __tablename__ = "tasks"

    name: Mapped[str]
    description: Mapped[str]
    points: Mapped[int]
    criteria: Mapped[str]
    image_url: Mapped[Optional[str]]

    players: Mapped[List["TaskStatus"]] = relationship(back_populates="task", cascade="all, delete")


class TaskStatus(Base):
    __tablename__ = "task_status"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    completed: Mapped[bool] = mapped_column(default=False)
    attempts: Mapped[int] = mapped_column(default=0)

    task: Mapped["Task"] = relationship()
    user: Mapped["User"] = relationship()


class Product(Base):
    __tablename__ = "products"

    name: Mapped[str]
    description: Mapped[Optional[str]]
    points: Mapped[int] = mapped_column(default=0)
    stock: Mapped[int] = mapped_column(default=0)
    image_url: Mapped[Optional[str]]


class Transaction(Base):
    __tablename__ = "transactions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[int]
    description: Mapped[Optional[str]]

    user: Mapped[User] = relationship()


class Message(Base):
    __tablename__ = "messages"

    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    message: Mapped[str]
    is_visible: Mapped[bool] = mapped_column(default=False)

    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    receiver: Mapped["User"] = relationship(foreign_keys=[receiver_id])

    def to_dict(self):
        return super().to_dict() | {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message": self.message,
            "is_visible": self.is_visible,
        }


class Rooms(Base):
    __tablename__ = "rooms"

    user_1: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user_2: Mapped[str] = mapped_column(ForeignKey("users.id"))