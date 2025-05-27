from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field, Relationship, Column, UniqueConstraint
from sqlalchemy import CheckConstraint, ForeignKey, Numeric


class Role(SQLModel, table=True):
    __tablename__ = 'roles'
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(
        "name",
        str,
        unique=True,
        nullable=False
    ))

    users: List["User"] = Relationship(back_populates="role")


class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(sa_column=Column(
        "username",
        str,
        unique=True,
        nullable=False
    ))
    password_hash: str = Field(nullable=False)
    role_id: int = Field(
        foreign_key="roles.id",
        nullable=False,
        sa_column=Column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    )
    full_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    role: Optional[Role] = Relationship(back_populates="users")
    group_memberships: List["GroupMember"] = Relationship(back_populates="user")
    assignments: List["Assignment"] = Relationship(back_populates="user")
    progress_entries: List["Progress"] = Relationship(back_populates="user")
    test_results: List["TestResult"] = Relationship(back_populates="user")


class Group(SQLModel, table=True):
    __tablename__ = 'groups_'
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(
        "name",
        str,
        unique=True,
        nullable=False
    ), index=True)

    members: List["GroupMember"] = Relationship(back_populates="group")
    assignments: List["Assignment"] = Relationship(back_populates="group")


class GroupMember(SQLModel, table=True):
    __tablename__ = 'group_members'
    group_id: int = Field(
        foreign_key="groups_.id",
        primary_key=True,
        sa_column=Column(ForeignKey("groups_.id", ondelete="CASCADE"))
    )
    user_id: int = Field(
        foreign_key="users.id",
        primary_key=True,
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"))
    )

    group: Optional[Group] = Relationship(back_populates="members")
    user: Optional[User] = Relationship(back_populates="group_memberships")


class Category(SQLModel, table=True):
    __tablename__ = 'categories'
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    parent_id: Optional[int] = Field(
        default=None,
        foreign_key="categories.id",
        sa_column=Column(ForeignKey("categories.id", ondelete="SET NULL")),
        index=True
    )

    children: List["Category"] = Relationship(back_populates="parent")
    parent: Optional["Category"] = Relationship(back_populates="children")
    articles: List["Article"] = Relationship(back_populates="category")
    tests: List["Test"] = Relationship(back_populates="category")
    assignments: List["Assignment"] = Relationship(back_populates="category")
    progress_entries: List["Progress"] = Relationship(back_populates="category")


class Article(SQLModel, table=True):
    __tablename__ = 'articles'
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        sa_column=Column(ForeignKey("categories.id", ondelete="CASCADE")),
        index=True
    )
    title: str = Field(nullable=False)
    content: str = Field(nullable=False)
    content_type: str = Field(
        sa_column=Column("content_type", str, nullable=False),
        regex="^(markdown|html)$"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    category: Optional[Category] = Relationship(back_populates="articles")
    media_items: List["Media"] = Relationship(back_populates="article")

    __table_args__ = (
        CheckConstraint(
            "content_type IN ('markdown','html')",
            name="chk_article_content_type"
        ),
    )


class Media(SQLModel, table=True):
    __tablename__ = 'media'
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(
        foreign_key="articles.id",
        nullable=False,
        sa_column=Column(ForeignKey("articles.id", ondelete="CASCADE")),
        index=True
    )
    media_type: str = Field(
        sa_column=Column("media_type", str, nullable=False),
        regex="^(svg|png|webm)$"
    )
    url: str = Field(nullable=False)
    sort_order: int = Field(default=0)

    article: Optional[Article] = Relationship(back_populates="media_items")

    __table_args__ = (
        CheckConstraint(
            "media_type IN ('svg','png','webm')",
            name="chk_media_media_type"
        ),
    )


class Test(SQLModel, table=True):
    __tablename__ = 'tests'
    id: Optional[int] = Field(default=None, primary_key=True)
    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        sa_column=Column(ForeignKey("categories.id", ondelete="CASCADE")),
        index=True
    )
    title: str = Field(nullable=False)
    max_attempts: int = Field(default=3)

    category: Optional[Category] = Relationship(back_populates="tests")
    questions: List["Question"] = Relationship(back_populates="test")
    results: List["TestResult"] = Relationship(back_populates="test")


class Question(SQLModel, table=True):
    __tablename__ = 'questions'
    id: Optional[int] = Field(default=None, primary_key=True)
    test_id: int = Field(
        foreign_key="tests.id",
        nullable=False,
        sa_column=Column(ForeignKey("tests.id", ondelete="CASCADE")),
        index=True
    )
    text: str = Field(nullable=False)
    weight: int = Field(default=1)

    test: Optional[Test] = Relationship(back_populates="questions")
    options: List["AnswerOption"] = Relationship(back_populates="question")
    answers: List["TestAnswer"] = Relationship(back_populates="question")


class AnswerOption(SQLModel, table=True):
    __tablename__ = 'answer_options'
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(
        foreign_key="questions.id",
        nullable=False,
        sa_column=Column(ForeignKey("questions.id", ondelete="CASCADE")),
        index=True
    )
    text: str = Field(nullable=False)
    is_correct: bool = Field(default=False)

    question: Optional[Question] = Relationship(back_populates="options")
    selected_answers: List["TestAnswer"] = Relationship(back_populates="selected_option")


class Assignment(SQLModel, table=True):
    __tablename__ = 'assignments'
    id: Optional[int] = Field(default=None, primary_key=True)
    assigned_by: int = Field(
        foreign_key="users.id",
        nullable=False,
        sa_column=Column(ForeignKey("users.id", ondelete="RESTRICT")),
        index=True
    )
    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        sa_column=Column(ForeignKey("categories.id", ondelete="CASCADE")),
        index=True
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="users.id",
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE")),
        index=True
    )
    group_id: Optional[int] = Field(
        default=None,
        foreign_key="groups_.id",
        sa_column=Column(ForeignKey("groups_.id", ondelete="CASCADE")),
        index=True
    )
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND group_id IS NULL) OR (user_id IS NULL AND group_id IS NOT NULL)",
            name="chk_assignment_single_target"
        ),
    )

    teacher: Optional[User] = Relationship(sa_relationship_kwargs={"primaryjoin": "User.id==Assignment.assigned_by"})
    category: Optional[Category] = Relationship(back_populates="assignments")
    user: Optional[User] = Relationship(back_populates="assignments", sa_relationship_kwargs={"primaryjoin": "User.id==Assignment.user_id"})
    group: Optional[Group] = Relationship(back_populates="assignments")


class Progress(SQLModel, table=True):
    __tablename__ = 'progress'
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE")),
        index=True
    )
    category_id: int = Field(
        foreign_key="categories.id",
        nullable=False,
        sa_column=Column(ForeignKey("categories.id", ondelete="CASCADE")),
        index=True
    )
    status: str = Field(
        sa_column=Column("status", str, nullable=False)
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started','in_progress','done')",
            name="chk_progress_status"
        ),
        UniqueConstraint("user_id", "category_id", name="uq_progress_user_category"),
    )

    user: Optional[User] = Relationship(back_populates="progress_entries")
    category: Optional[Category] = Relationship(back_populates="progress_entries")


class TestResult(SQLModel, table=True):
    __tablename__ = 'test_results'
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        nullable=False,
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE")),
        index=True
    )
    test_id: int = Field(
        foreign_key="tests.id",
        nullable=False,
        sa_column=Column(ForeignKey("tests.id", ondelete="CASCADE")),
        index=True
    )
    score: Decimal = Field(
        sa_column=Column(Numeric(5,2), nullable=False)
    )
    max_score: Decimal = Field(
        sa_column=Column(Numeric(5,2), nullable=False)
    )
    passed: bool = Field(nullable=False)
    taken_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="test_results")
    test: Optional[Test] = Relationship(back_populates="results")
    answers: List["TestAnswer"] = Relationship(back_populates="test_result")


class TestAnswer(SQLModel, table=True):
    __tablename__ = 'test_answers'
    id: Optional[int] = Field(default=None, primary_key=True)
    test_result_id: int = Field(
        foreign_key="test_results.id",
        nullable=False,
        sa_column=Column(ForeignKey("test_results.id", ondelete="CASCADE")),
        index=True
    )
    question_id: int = Field(
        foreign_key="questions.id",
        nullable=False,
        sa_column=Column(ForeignKey("questions.id", ondelete="CASCADE")),
        index=True
    )
    selected_option_id: int = Field(
        foreign_key="answer_options.id",
        nullable=False,
        sa_column=Column(ForeignKey("answer_options.id", ondelete="CASCADE")),
        index=True
    )

    test_result: Optional[TestResult] = Relationship(back_populates="answers")
    question: Optional[Question] = Relationship(back_populates="answers")
    selected_option: Optional[AnswerOption] = Relationship(back_populates="selected_answers")
