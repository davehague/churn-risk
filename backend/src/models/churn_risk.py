from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class TriggerType(str, enum.Enum):
    """Types of churn risk triggers."""
    FRUSTRATED = "frustrated"
    SIGNIFICANT_SUPPORT = "significant_support"
    SILENTLY_STRUGGLING = "silently_struggling"


class ChurnRiskStatus(str, enum.Enum):
    """Churn risk card status."""
    NEW = "new"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"


class ChurnRiskCard(Base, UUIDMixin, TimestampMixin):
    """Churn risk card model - Kanban cards for at-risk customers."""
    __tablename__ = "churn_risk_cards"
    __table_args__ = (
        Index("ix_churn_risks_tenant_status", "tenant_id", "status", "created_at"),
    )

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type = Column(SQLEnum(TriggerType), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True)  # Triggering ticket

    status = Column(SQLEnum(ChurnRiskStatus), default=ChurnRiskStatus.NEW, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="churn_risks")
    company = relationship("Company", back_populates="churn_risks")
    contact = relationship("Contact", back_populates="churn_risks")
    ticket = relationship("Ticket", back_populates="churn_risk")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_churn_risks")
    comments = relationship("ChurnRiskComment", back_populates="card", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChurnRiskCard {self.trigger_type} for company {self.company_id}>"


class ChurnRiskComment(Base, UUIDMixin, TimestampMixin):
    """Comment on a churn risk card."""
    __tablename__ = "churn_risk_comments"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("churn_risk_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    mentions = Column(ARRAY(UUID(as_uuid=True)), default=list)  # User IDs tagged

    # Relationships
    tenant = relationship("Tenant")
    card = relationship("ChurnRiskCard", back_populates="comments")
    user = relationship("User", back_populates="comments")

    def __repr__(self):
        return f"<Comment on card {self.card_id} by user {self.user_id}>"
