"""Models package - exports all database models and enums."""

# Base models and mixins
from src.models.base import Base, TimestampMixin, UUIDMixin

# Tenant model
from src.models.tenant import Tenant, PlanTier

# User model
from src.models.user import User, UserRole

# Integration models
from src.models.integration import Integration, IntegrationType, IntegrationStatus

# Company and Contact models
from src.models.company import Company
from src.models.contact import Contact

# Ticket models
from src.models.ticket import Ticket, TicketStatus, SentimentScore

# Topic models
from src.models.topic import TicketTopic, TicketTopicAssignment, AssignedBy

# Churn risk models
from src.models.churn_risk import (
    ChurnRiskCard,
    ChurnRiskComment,
    ChurnRiskStatus,
    TriggerType,
)

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Tenant
    "Tenant",
    "PlanTier",
    # User
    "User",
    "UserRole",
    # Integration
    "Integration",
    "IntegrationType",
    "IntegrationStatus",
    # Company and Contact
    "Company",
    "Contact",
    # Ticket
    "Ticket",
    "TicketStatus",
    "SentimentScore",
    # Topic
    "TicketTopic",
    "TicketTopicAssignment",
    "AssignedBy",
    # Churn Risk
    "ChurnRiskCard",
    "ChurnRiskComment",
    "ChurnRiskStatus",
    "TriggerType",
]
