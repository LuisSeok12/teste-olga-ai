from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TIMESTAMP,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ============================
# Customers
# ============================
class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    policies: Mapped[List["Policy"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sinistros: Mapped[List["Sinistro"]] = relationship(
        back_populates="customer",
        lazy="selectin",
    )


# ============================
# Policies
# ============================
class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    policy_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )  # ('ACTIVE','INACTIVE','CANCELLED')
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','INACTIVE','CANCELLED')", name="policies_status_check"),
    )

    customer: Mapped["Customer"] = relationship(back_populates="policies")


# ============================
# Atendimento Queue
# ============================
class AtendimentoQueue(Base):
    __tablename__ = "atendimento_queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="AGUARDANDO",
    )  # ('AGUARDANDO','PROCESSANDO','CONCLUIDO','ERRO')
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('AGUARDANDO','PROCESSANDO','CONCLUIDO','ERRO')",
            name="queue_status_check",
        ),
        Index("idx_queue_status_priority", "status", "priority", "created_at"),
        Index("idx_queue_phone", "phone"),
    )


# ============================
# Sinistros
# ============================
class Sinistro(Base):
    __tablename__ = "sinistros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("customers.id"))
    protocol: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="OPEN",
    )  # ('OPEN','IN_REVIEW','CLOSED','REJECTED')
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN','IN_REVIEW','CLOSED','REJECTED')",
            name="sinistros_status_check",
        ),
    )

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="sinistros")


# ============================
# User Sessions
# ============================
class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(Text, nullable=False)
    session_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
