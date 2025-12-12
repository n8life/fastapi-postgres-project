from uuid import UUID
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, and_, or_, update, func

from ..database import db_manager
from ..schemas.messaging import (
    AgentCreate, AgentUpdate, AgentRead,
    MessageCreate, MessageUpdate, MessageRead,
    MessageRecipientCreate, MessageRecipientUpdate, MessageRecipientRead,
    AgentMessageMetadataCreate, AgentMessageMetadataUpdate, AgentMessageMetadataRead,
    MessageWithRecipientInfo, MessageMetadataWithAgent, MarkAsReadRequest, MarkAsReadResponse,
    ConversationCreate, ConversationUpdate, ConversationRead, ConversationWithMessages,
)
from ..models.messaging import Agent, Message, MessageRecipient, AgentMessageMetadata, Conversation, TimedMessage
from ..security import get_api_key


router = APIRouter(prefix="", tags=["messaging"])


# Agents endpoints
@router.post("/agents", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreate, api_key: str = Depends(get_api_key)):
    """Create a new agent"""
    async with db_manager.get_connection() as session:
        try:
            agent = Agent(**payload.model_dump())
            session.add(agent)
            await session.commit()
            await session.refresh(agent)
            return agent
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent creation failed due to constraint violation"
            )


@router.put("/agents/{agent_id}", response_model=AgentRead)
async def update_agent(agent_id: UUID, payload: AgentUpdate, api_key: str = Depends(get_api_key)):
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
async def create_message(payload: MessageCreate, api_key: str = Depends(get_api_key)):
    """Create a new message"""
    async with db_manager.get_connection() as session:
        try:
            # Extract schedule_at before creating message
            message_data = payload.model_dump()
            schedule_at = message_data.pop("schedule_at", None)
            
            message = Message(**message_data)
            session.add(message)
            await session.flush()  # flush to get message.id
            
            if schedule_at:
                timed_msg = TimedMessage(message_id=message.id, send_at=schedule_at)
                session.add(timed_msg)
                
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
async def update_message(message_id: UUID, payload: MessageUpdate, api_key: str = Depends(get_api_key)):
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
async def create_message_recipient(payload: MessageRecipientCreate, api_key: str = Depends(get_api_key)):
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
async def update_message_recipient(message_id: UUID, recipient_id: UUID, payload: MessageRecipientUpdate, api_key: str = Depends(get_api_key)):
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
async def create_agent_message_metadata(payload: AgentMessageMetadataCreate, api_key: str = Depends(get_api_key)):
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
async def update_agent_message_metadata(metadata_id: UUID, payload: AgentMessageMetadataUpdate, api_key: str = Depends(get_api_key)):
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
async def get_all_messages_for_agent(agent_id: UUID, api_key: str = Depends(get_api_key)):
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
        ).outerjoin(
            TimedMessage,
            Message.id == TimedMessage.message_id
        ).where(
            or_(
                TimedMessage.message_id.is_(None),
                TimedMessage.send_at <= func.now()
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
async def get_unread_messages_for_agent(agent_id: UUID, api_key: str = Depends(get_api_key)):
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
        ).outerjoin(
            TimedMessage,
            Message.id == TimedMessage.message_id
        ).where(
            and_(
                MessageRecipient.recipient_id == agent_id,
                or_(MessageRecipient.is_read == False, MessageRecipient.is_read.is_(None)),
                or_(
                    TimedMessage.message_id.is_(None),
                    TimedMessage.send_at <= func.now()
                )
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
async def get_message_metadata_with_agent(message_id: UUID, agent_id: UUID, api_key: str = Depends(get_api_key)):
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
async def mark_messages_as_read(agent_id: UUID, payload: MarkAsReadRequest, api_key: str = Depends(get_api_key)):
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


# Conversation endpoints
@router.post("/conversations", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, api_key: str = Depends(get_api_key)):
    """Create a new conversation"""
    async with db_manager.get_connection() as session:
        try:
            # Convert payload to use correct field name
            data = payload.model_dump(by_alias=False)
            conversation = Conversation(**data)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            
            # Return properly mapped response
            return ConversationRead(
                id=conversation.id,
                created_at=conversation.created_at,
                title=conversation.title,
                description=conversation.description,
                archived=conversation.archived,
                conv_metadata=conversation.conv_metadata
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conversation creation failed due to constraint violation"
            )


@router.put("/conversations/{conversation_id}", response_model=ConversationRead)
async def update_conversation(conversation_id: UUID, payload: ConversationUpdate, api_key: str = Depends(get_api_key)):
    """Update an existing conversation"""
    async with db_manager.get_connection() as session:
        conversation = await session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Conversation not found"
            )
        
        try:
            update_data = payload.model_dump(exclude_unset=True, by_alias=False)
            for key, value in update_data.items():
                setattr(conversation, key, value)
            
            await session.commit()
            await session.refresh(conversation)
            
            # Return properly mapped response
            return ConversationRead(
                id=conversation.id,
                created_at=conversation.created_at,
                title=conversation.title,
                description=conversation.description,
                archived=conversation.archived,
                conv_metadata=conversation.conv_metadata
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conversation update failed due to constraint violation"
            )


@router.get("/conversations", response_model=List[ConversationRead])
async def list_conversations(api_key: str = Depends(get_api_key)):
    """List all conversations"""
    async with db_manager.get_connection() as session:
        result = await session.execute(select(Conversation).order_by(Conversation.created_at.desc()))
        conversations = result.scalars().all()
        
        # Return properly mapped responses
        return [
            ConversationRead(
                id=conv.id,
                created_at=conv.created_at,
                title=conv.title,
                description=conv.description,
                archived=conv.archived,
                conv_metadata=conv.conv_metadata
            )
            for conv in conversations
        ]


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(conversation_id: UUID, api_key: str = Depends(get_api_key)):
    """Get a single conversation by ID"""
    async with db_manager.get_connection() as session:
        conversation = await session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Return properly mapped response
        return ConversationRead(
            id=conversation.id,
            created_at=conversation.created_at,
            title=conversation.title,
            description=conversation.description,
            archived=conversation.archived,
            conv_metadata=conversation.conv_metadata
        )


@router.get("/conversations/{conversation_id}/details", response_model=ConversationWithMessages)
async def get_conversation_details(conversation_id: UUID, api_key: str = Depends(get_api_key)):
    """Get comprehensive conversation info including all messages, agents, and metadata"""
    async with db_manager.get_connection() as session:
        # Get conversation
        conversation = await session.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get all messages in conversation with recipients info
        messages_stmt = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.sent_at.asc())
        
        messages_result = await session.execute(messages_stmt)
        messages = messages_result.scalars().all()
        
        # Get all unique agents involved in the conversation (senders + recipients)
        # First get sender agent IDs from messages in this conversation
        sender_ids_stmt = select(Message.sender_id).where(
            and_(
                Message.conversation_id == conversation_id,
                Message.sender_id.is_not(None)
            )
        )
        
        # Then get recipient agent IDs from message_recipients for messages in this conversation
        recipient_ids_stmt = select(MessageRecipient.recipient_id).join(
            Message, Message.id == MessageRecipient.message_id
        ).where(Message.conversation_id == conversation_id)
        
        # Get agents who are either senders or recipients
        agents_stmt = select(Agent).where(
            or_(
                Agent.id.in_(sender_ids_stmt),
                Agent.id.in_(recipient_ids_stmt)
            )
        )
        
        agents_result = await session.execute(agents_stmt)
        unique_agents = agents_result.scalars().all()
        
        # Count unread messages in conversation
        unread_stmt = select(MessageRecipient).join(
            Message, Message.id == MessageRecipient.message_id
        ).where(
            and_(
                Message.conversation_id == conversation_id,
                or_(MessageRecipient.is_read == False, MessageRecipient.is_read.is_(None))
            )
        )
        
        unread_result = await session.execute(unread_stmt)
        unread_count = len(unread_result.scalars().all())
        
        # Build response
        conversation_dict = {
            "id": conversation.id,
            "created_at": conversation.created_at,
            "archived": conversation.archived,
            "title": conversation.title,
            "description": conversation.description,
            "conv_metadata": conversation.conv_metadata,
        }
        
        message_dicts = []
        for msg in messages:
            message_dicts.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sent_at": msg.sent_at,
                "parent_message_id": msg.parent_message_id,
                "conversation_id": msg.conversation_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "importance": msg.importance,
                "status": msg.status,
                "msg_metadata": msg.msg_metadata,
            })
        
        agent_dicts = []
        for agent in unique_agents:
            agent_dicts.append({
                "id": agent.id,
                "agent_name": agent.agent_name,
                "ip_address": agent.ip_address,
                "port": agent.port,
                "created_at": agent.created_at,
            })
        
        return ConversationWithMessages(
            **conversation_dict,
            messages=[MessageRead(**msg) for msg in message_dicts],
            unique_agents=[AgentRead(**agent) for agent in agent_dicts],
            total_messages=len(messages),
            unread_count=unread_count
        )
