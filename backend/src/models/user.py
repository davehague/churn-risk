from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from src.models.base import Base, UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """User model - people at each tenant company."""
    __tablename__ = "users"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    owned_churn_risks = relationship("ChurnRiskCard", foreign_keys="ChurnRiskCard.owner_id", back_populates="owner")
    comments = relationship("ChurnRiskComment", back_populates="user")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
