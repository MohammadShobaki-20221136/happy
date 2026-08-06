from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("user_id", UUID(as_uuid=True), primary_key=True,
           server_default=text("gen_random_uuid()")),
    Column("name", String, nullable=False),
    Column("email", String, nullable=False, unique=True),
    Column("password", String, nullable=False),
    Column("created_at", TIMESTAMP, nullable=False,
           server_default=text("CURRENT_TIMESTAMP")),
    Column("last_login", TIMESTAMP),
)

history = Table(
    "history",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           server_default=text("gen_random_uuid()")),
    Column("user_id", UUID(as_uuid=True),
           ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
    Column("input_text", Text, nullable=False),
    Column("sentiment_label", String, nullable=False),
    Column("confidence_score", Float, nullable=False, server_default=text("0")),
    Column("created_at", TIMESTAMP, nullable=False,
           server_default=text("CURRENT_TIMESTAMP")),
    Column("Deleted", Boolean, nullable=False, server_default=text("false")),
    CheckConstraint(
        "sentiment_label IN ('positive', 'negative', 'neutral')",
        name="ck_history_sentiment_label",
    ),
)


word_bank = Table(
    "word_bank",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           server_default=text("gen_random_uuid()")),
    Column("word", String, nullable=False, unique=True),
    Column("category", String, nullable=False),
    Column("weight", Integer, nullable=False, server_default=text("1")),
    Column("created_at", TIMESTAMP, nullable=False,
           server_default=text("CURRENT_TIMESTAMP")),
    Column("Deleted", Boolean, nullable=False, server_default=text("false")),
    CheckConstraint(
        "category IN ('happy', 'sad')",
        name="ck_word_bank_category",
    ),
)