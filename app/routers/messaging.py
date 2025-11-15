from uuid import UUID
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

from ..database import db_manager
from ..schemas.messaging import (
    AgentCreate, AgentUpdate, AgentRead,
    MessageCreate, MessageUpdate, MessageRead,
    MessageRecipientCreate, MessageRecipientUpdate, MessageRecipientRead,
    AgentMessageMetadataCreate, AgentMessageMetadataUpdate, AgentMessageMetadataRead,
    MessageWithRecipientInfo, MessageMetadataWithAgent, MarkAsReadRequest, MarkAsReadResponse,
)
from ..models.messaging import Agent, Message, MessageRecipient, AgentMessageMetadata


router = APIRouter(prefix="", tags=["messaging"])


# Agents endpoints
@router.post("/agents", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate):
    """Create a new agent"""
    async with db_manager.get_connection() as session:
        try:
            agent = Agent(**payload.model_dump())
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            return agent
        except IntegrityError as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent creation failed due to constraint violation"
            )


@router.put("/agents/{agent_id}", response_model=AgentRead)
async def update_agent(agent_id: UUID, payload: AgentUpdate):
    """Update an existing agent"""
    async with db_manager.get_connection() as session:
        agent = await session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Agent not found"
            )
        
        try:
            update_data = payload.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(agent, key, value)
            
            await session.commit()
            await session.refresh(agent)
            return agent
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent update failed due to constraint violation"
            )


# Messages endpoints
@router.post("/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(payload: MessageCreate):
    """Create a new message"""
    async with db_manager.get_connection() as session:
        try:
            message = Message(**payload.model_dump())
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Message creation failed - sender agent may not exist"
            )


@router.put("/messages/{message_id}", response_model=MessageRead)
async def update_message(message_id: UUID, payload: MessageUpdate):
    """Update an existing message"""
    async with db_manager.get_connection() as session:
        message = await session.get(Message, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        try:
            update_data = payload.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(message, key, value)
            
            await session.commit()
            await session.refresh(message)
            return message
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Message update failed due to constraint violation"
            )


# MessageRecipients endpoints (composite key handling)
@router.post("/message_recipients", response_model=MessageRecipientRead, status_code=status.HTTP_201_CREATED)
async def create_message_recipient(payload: MessageRecipientCreate):
    """Create a new message recipient relationship"""
    async with db_manager.get_connection() as session:
        try:
            recipient = MessageRecipient(**payload.model_dump())
            session.add(recipient)
            await session.commit()
            await session.refresh(recipient)
            return recipient
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Recipient relationship already exists or referenced entities not found"
            )


@router.put("/message_recipients/{message_id}/{recipient_id}", response_model=MessageRecipientRead)
async def update_message_recipient(message_id: UUID, recipient_id: UUID, payload: MessageRecipientUpdate):
    """Update an existing message recipient relationship (composite key)"""
    async with db_manager.get_connection() as session:
        recipient = await session.get(MessageRecipient, (message_id, recipient_id))
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message recipient relationship not found"
            )
        
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(recipient, key, value)
        
        await session.commit()
        await session.refresh(recipient)
        return recipient


# AgentMessageMetadata endpoints
@router.post("/agent_message_metadata", response_model=AgentMessageMetadataRead, status_code=status.HTTP_201_CREATED)
async def create_agent_message_metadata(payload: AgentMessageMetadataCreate):
    """Create new agent message metadata"""
    async with db_manager.get_connection() as session:
        try:
            metadata = AgentMessageMetadata(**payload.model_dump())
            session.add(metadata)
            await session.commit()
            await session.refresh(metadata)
            return metadata
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Metadata creation failed - message may not exist"
            )


@router.put("/agent_message_metadata/{metadata_id}", response_model=AgentMessageMetadataRead)
async def update_agent_message_metadata(metadata_id: UUID, payload: AgentMessageMetadataUpdate):
    """Update existing agent message metadata"""
    async with db_manager.get_connection() as session:
        metadata = await session.get(AgentMessageMetadata, metadata_id)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent message metadata not found"
            )
        
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(metadata, key, value)
        
        await session.commit()
        await session.refresh(metadata)
        return metadata


# Message pulling endpoints for Feature 3
@router.get("/agents/{agent_id}/messages", response_model=List[MessageWithRecipientInfo])
async def get_all_messages_for_agent(agent_id: UUID):
    """Get all messages by looking up by recipient_id in message_recipients for an agent"""
    async with db_manager.get_connection() as session:
        # Verify agent exists
        agent = await session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Query for messages where agent is recipient (per spec: lookup by recipient_id)
        stmt = select(Message, MessageRecipient.is_read, MessageRecipient.read_at).join(
            MessageRecipient,
            and_(
                Message.id == MessageRecipient.message_id,
                MessageRecipient.recipient_id == agent_id
            )
        ).order_by(Message.sent_at.desc())
        
        result = await session.execute(stmt)
        messages_data = result.all()
        
        messages_with_info = []
        for message, is_read, read_at in messages_data:
            message_dict = {
                "id": message.id,
                "sender_id": message.sender_id,
                "sent_at": message.sent_at,
                "parent_message_id": message.parent_message_id,
                "conversation_id": message.conversation_id,
                "content": message.content,
                "message_type": message.message_type,
                "importance": message.importance,
                "status": message.status,
                "msg_metadata": message.msg_metadata,
                "is_read": is_read,  # All messages are received messages now
                "read_at": read_at,
            }
            messages_with_info.append(MessageWithRecipientInfo(**message_dict))
        
        return messages_with_info


@router.get("/agents/{agent_id}/messages/unread", response_model=List[MessageWithRecipientInfo])
async def get_unread_messages_for_agent(agent_id: UUID):
    """Get all unread messages for a specific agent"""
    async with db_manager.get_connection() as session:
        # Verify agent exists
        agent = await session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Query for unread messages where agent is recipient
        stmt = select(Message, MessageRecipient.is_read, MessageRecipient.read_at).join(
            MessageRecipient,
            and_(
                Message.id == MessageRecipient.message_id,
                MessageRecipient.recipient_id == agent_id
            )
        ).where(
            and_(
                MessageRecipient.recipient_id == agent_id,
                or_(MessageRecipient.is_read == False, MessageRecipient.is_read.is_(None))
            )
        ).order_by(Message.sent_at.desc())
        
        result = await session.execute(stmt)
        messages_data = result.all()
        
        messages_with_info = []
        for message, is_read, read_at in messages_data:
            message_dict = {
                "id": message.id,
                "sender_id": message.sender_id,
                "sent_at": message.sent_at,
                "parent_message_id": message.parent_message_id,
                "conversation_id": message.conversation_id,
                "content": message.content,
                "message_type": message.message_type,
                "importance": message.importance,
                "status": message.status,
                "msg_metadata": message.msg_metadata,
                "is_read": is_read,
                "read_at": read_at,
            }
            messages_with_info.append(MessageWithRecipientInfo(**message_dict))
        
        return messages_with_info


@router.get("/messages/{message_id}/metadata/{agent_id}", response_model=MessageMetadataWithAgent)
async def get_message_metadata_with_agent(message_id: UUID, agent_id: UUID):
    """Get message metadata and agent info - agent can only access their own messages"""
    async with db_manager.get_connection() as session:
        # Verify agent exists
        agent = await session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Get message and verify agent has access (sender or recipient)
        message = await session.get(Message, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Check if agent has access to this message
        has_access = False
        if message.sender_id == agent_id:
            has_access = True
        else:
            # Check if agent is a recipient
            recipient_check = await session.get(MessageRecipient, (message_id, agent_id))
            if recipient_check:
                has_access = True
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent does not have access to this message"
            )
        
        # Get metadata items for this message
        metadata_stmt = select(AgentMessageMetadata).where(
            AgentMessageMetadata.message_id == message_id
        )
        metadata_result = await session.execute(metadata_stmt)
        metadata_items = metadata_result.scalars().all()
        
        # Build response
        message_dict = {
            "id": message.id,
            "sender_id": message.sender_id,
            "sent_at": message.sent_at,
            "parent_message_id": message.parent_message_id,
            "conversation_id": message.conversation_id,
            "content": message.content,
            "message_type": message.message_type,
            "importance": message.importance,
            "status": message.status,
            "msg_metadata": message.msg_metadata,
        }
        
        agent_dict = {
            "id": agent.id,
            "agent_name": agent.agent_name,
            "ip_address": agent.ip_address,
            "port": agent.port,
            "created_at": agent.created_at,
        }
        
        metadata_dicts = []
        for item in metadata_items:
            metadata_dicts.append({
                "id": item.id,
                "message_id": item.message_id,
                "key": item.key,
                "value": item.value,
                "created_at": item.created_at,
            })
        
        response_data = {
            "message_id": message_id,
            "message": MessageRead(**message_dict),
            "agent": AgentRead(**agent_dict),
            "metadata_items": [AgentMessageMetadataRead(**item) for item in metadata_dicts],
        }
        
        return MessageMetadataWithAgent(**response_data)


@router.put("/agents/{agent_id}/messages/mark-read", response_model=MarkAsReadResponse)
async def mark_messages_as_read(agent_id: UUID, payload: MarkAsReadRequest):
    """Mark all messages as read for an agent up to a specific date"""
    async with db_manager.get_connection() as session:
        # Verify agent exists
        agent = await session.get(Agent, agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Find message IDs to update using subquery
        message_ids_subquery = select(MessageRecipient.message_id).join(
            Message, Message.id == MessageRecipient.message_id
        ).where(
            and_(
                MessageRecipient.recipient_id == agent_id,
                Message.sent_at <= payload.read_up_to_date,
                or_(MessageRecipient.is_read == False, MessageRecipient.is_read.is_(None))
            )
        )
        
        # Update messages as read up to the specified date
        stmt = update(MessageRecipient).where(
            and_(
                MessageRecipient.recipient_id == agent_id,
                MessageRecipient.message_id.in_(message_ids_subquery)
            )
        ).values(
            is_read=True,
            read_at=datetime.now()
        )
        
        # Execute the update and get count
        result = await session.execute(stmt)
        updated_count = result.rowcount
        await session.commit()
        
        return MarkAsReadResponse(
            updated_count=updated_count,
            message=f"Marked {updated_count} messages as read for agent {agent_id}"
        )
