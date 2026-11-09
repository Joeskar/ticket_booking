from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.db.base import Base
from infrastructure.db.mixins import TimeStampMixin, UuidMixin


class PaymentStatus(StrEnum):
    PENDING = "PENDING"      
    SUCCEEDED = "SUCCEEDED"  
    EXPIRED = "EXPIRED"     


class AttemptStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Payment(Base, UuidMixin, TimeStampMixin):
    booking_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False), nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class PaymentAttempt(Base, UuidMixin, TimeStampMixin):
    payment_id: Mapped[UUID] = mapped_column(
        ForeignKey("payments.id"), nullable=False
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    status: Mapped[AttemptStatus] = mapped_column(
        SAEnum(AttemptStatus, native_enum=False), nullable=False
    )

    card_last4: Mapped[str] = mapped_column(
        String(4), nullable=False
    )

    failure_reason: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    provider_ref: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("payment_id", "idempotency_key", name="uq_payment_attempts_key"),
        Index(
            "uq_payment_attempts_one_success",
            "payment_id",
            unique=True,
            postgresql_where=text("status = 'SUCCEEDED'"),
        ),
    )
