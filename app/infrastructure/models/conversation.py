"""
Modelos ORM para el sistema de historial de conversaciones.
Define las tablas: conversations e interactions.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.models.producto import Base


class ConversationModel(Base):
    """Modelo ORM para tabla conversations"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    total_interactions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    interactions = relationship(
        "InteractionModel",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class InteractionModel(Base):
    """Modelo ORM para tabla interactions"""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    intent_type = Column(String(50), nullable=False, index=True)
    response_source = Column(String(50), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relaciones
    conversation = relationship("ConversationModel", back_populates="interactions")
