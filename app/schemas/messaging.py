from __future__ import annotations

from typing import Optional, Any, Union
from uuid import UUID
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address
from pydantic import BaseModel, ConfigDict, IPvAnyAddress, Field, field_serializer


# Agents
class AgentBase(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")
    ip_address: Optional[str] = Field(None, description="IP address of the agent")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number")


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    agent_name: Optional[str] = Field(None, description="Name of the agent")
    ip_address: Optional[str] = Field(None, description="IP address of the agent")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number")


class AgentRead(BaseModel):
    id: UUID
    agent_name: str
    ip_address: Optional[Union[str, IPv4Address, IPv6Address]] = None
    port: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_serializer('ip_address')
    def serialize_ip_address(self, value: Optional[Union[str, IPv4Address, IPv6Address]]) -> Optional[str]:
        if value is None:
            return None
        return str(value)


# Messages
class MessageBase(BaseModel):
    content: str = Field(..., description="Message content")
    sender_id: Optional[UUID] = Field(None, description="Sender agent ID")
    parent_message_id: Optional[UUID] = Field(None, description="Parent message ID for threading")
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID for grouping")
    message_type: Optional[str] = Field(None, description="Type of message")
    importance: Optional[int] = Field(None, ge=0, le=10, description="Message importance (0-10)")
    status: Optional[str] = Field(None, description="Message status")
    msg_metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class MessageCreate(MessageBase):
    pass


class MessageUpdate(BaseModel):
    content: Optional[str] = Field(None, description="Message content")
    parent_message_id: Optional[UUID] = Field(None, description="Parent message ID for threading")
    conversation_id: Optional[UUID] = Field(None, description="Conversation ID for grouping")
    message_type: Optional[str] = Field(None, description="Type of message")
    importance: Optional[int] = Field(None, ge=0, le=10, description="Message importance (0-10)")
    status: Optional[str] = Field(None, description="Message status")
    msg_metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class MessageRead(BaseModel):
    id: UUID
    sender_id: Optional[UUID]
    sent_at: Optional[datetime]
    parent_message_id: Optional[UUID]
    conversation_id: Optional[UUID]
    content: str
    message_type: Optional[str]
    importance: Optional[int]
    status: Optional[str]
    msg_metadata: Optional[dict[str, Any]]
    model_config = ConfigDict(from_attributes=True)


class MessageWithConversation(MessageRead):
    """Message with conversation information included"""
    conversation: Optional[ConversationRead] = None
    model_config = ConfigDict(from_attributes=True)


# MessageRecipients (composite key model)
class MessageRecipientBase(BaseModel):
    message_id: UUID = Field(..., description="Message ID")
    recipient_id: UUID = Field(..., description="Recipient agent ID")
    is_read: Optional[bool] = Field(False, description="Whether the message has been read")
    read_at: Optional[datetime] = Field(None, description="When the message was read")


class MessageRecipientCreate(MessageRecipientBase):
    pass


class MessageRecipientUpdate(BaseModel):
    is_read: Optional[bool] = Field(None, description="Whether the message has been read")
    read_at: Optional[datetime] = Field(None, description="When the message was read")


class MessageRecipientRead(MessageRecipientBase):
    model_config = ConfigDict(from_attributes=True)


# AgentMessageMetadata
class AgentMessageMetadataBase(BaseModel):
    message_id: Optional[UUID] = Field(None, description="Message ID")
    key: str = Field(..., description="Metadata key")
    value: Optional[str] = Field(None, description="Metadata value")


class AgentMessageMetadataCreate(AgentMessageMetadataBase):
    pass


class AgentMessageMetadataUpdate(BaseModel):
    key: Optional[str] = Field(None, description="Metadata key")
    value: Optional[str] = Field(None, description="Metadata value")


class AgentMessageMetadataRead(AgentMessageMetadataBase):
    id: UUID
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# Extended schemas for message pulling feature
class MessageWithRecipientInfo(MessageRead):
    """Message with recipient information for the requesting agent"""
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MessageMetadataWithAgent(BaseModel):
    """Message metadata combined with agent information"""
    message_id: UUID
    message: MessageRead
    agent: AgentRead
    metadata_items: list[AgentMessageMetadataRead]
    model_config = ConfigDict(from_attributes=True)


class MarkAsReadRequest(BaseModel):
    """Request to mark messages as read up to a specific date"""
    read_up_to_date: datetime = Field(..., description="Mark all messages as read up to this date")
    model_config = ConfigDict(from_attributes=True)


class MarkAsReadResponse(BaseModel):
    """Response for mark as read operation"""
    updated_count: int = Field(..., description="Number of messages marked as read")
    message: str = Field(..., description="Success message")
    model_config = ConfigDict(from_attributes=True)


# Conversation schemas
class ConversationBase(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title")
    description: Optional[str] = Field(None, description="Conversation description")
    archived: Optional[bool] = Field(False, description="Whether conversation is archived")
    conv_metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata as JSON", alias="metadata")
    model_config = ConfigDict(populate_by_name=True)


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Conversation title")
    description: Optional[str] = Field(None, description="Conversation description")
    archived: Optional[bool] = Field(None, description="Whether conversation is archived")
    conv_metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata as JSON", alias="metadata")
    model_config = ConfigDict(populate_by_name=True)


class ConversationRead(ConversationBase):
    id: UUID
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ConversationWithMessages(ConversationRead):
    """Conversation with all related messages, agents, and metadata"""
    messages: list[MessageRead]
    unique_agents: list[AgentRead] = Field(..., description="All agents involved in this conversation")
    total_messages: int = Field(..., description="Total number of messages in conversation")
    unread_count: int = Field(..., description="Number of unread messages")
    model_config = ConfigDict(from_attributes=True)
