from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Integer, Boolean, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conv_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    messages_sent: Mapped[List["Message"]] = relationship(
        "Message", 
        back_populates="sender", 
        foreign_keys="Message.sender_id"
    )
    message_recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", 
        back_populates="recipient"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    sender_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("agents.id"),
        nullable=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    parent_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("messages.id"),
        nullable=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("conversations.id"),
        nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    importance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    msg_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    sender: Mapped[Optional["Agent"]] = relationship(
        "Agent", 
        back_populates="messages_sent",
        foreign_keys=[sender_id]
    )
    parent: Mapped[Optional["Message"]] = relationship(
        "Message", 
        remote_side="Message.id"
    )
    recipients: Mapped[List["MessageRecipient"]] = relationship(
        "MessageRecipient", 
        back_populates="message"
    )
    metadata_items: Mapped[List["AgentMessageMetadata"]] = relationship(
        "AgentMessageMetadata", 
        back_populates="message"
    )
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", 
        back_populates="messages"
    )
    timed_message: Mapped[Optional["TimedMessage"]] = relationship(
        "TimedMessage",
        back_populates="message",
        cascade="all, delete-orphan",
        uselist=False
    )


class MessageRecipient(Base):
    __tablename__ = "message_recipients"

    # Composite primary key as per the SQL schema
    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("messages.id"),
        primary_key=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("agents.id"),
        primary_key=True
    )
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message", 
        back_populates="recipients"
    )
    recipient: Mapped["Agent"] = relationship(
        "Agent", 
        back_populates="message_recipients"
    )


class AgentMessageMetadata(Base):
    __tablename__ = "agent_message_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("messages.id"),
        nullable=True
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )

    # Relationships
    message: Mapped[Optional["Message"]] = relationship(
        "Message", 
        back_populates="metadata_items"
    )


class TimedMessage(Base):
    __tablename__ = "timed_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("messages.id"),
        primary_key=True
    )
    send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship(
        "Message", 
        back_populates="timed_message"
    )
