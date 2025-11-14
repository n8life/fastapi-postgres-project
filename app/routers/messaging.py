from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from ..database import db_manager
from ..schemas.messaging import (
    AgentCreate, AgentUpdate, AgentRead,
    MessageCreate, MessageUpdate, MessageRead,
    MessageRecipientCreate, MessageRecipientUpdate, MessageRecipientRead,
    AgentMessageMetadataCreate, AgentMessageMetadataUpdate, AgentMessageMetadataRead,
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