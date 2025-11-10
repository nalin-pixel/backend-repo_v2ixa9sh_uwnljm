"""
Database Schemas for AI-driven Wealth CRM

Each Pydantic model below represents a MongoDB collection. The collection
name equals the lowercase class name.

This system centers on advisors, households, clients, accounts, notes,
recommendations, tasks, communications, documents, and compliance logs.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Advisor(BaseModel):
    name: str = Field(..., description="Advisor full name")
    email: str = Field(..., description="Advisor email")
    role: str = Field("advisor", description="Role within the firm")
    crd_number: Optional[str] = Field(None, description="CRD/IARD number")
    teams: List[str] = Field(default_factory=list, description="Teams advisor belongs to")
    permissions: List[str] = Field(default_factory=list, description="Permission scopes")


class Household(BaseModel):
    name: str = Field(..., description="Household display name")
    primary_contact_id: Optional[str] = Field(None, description="Client ID of primary contact")
    members: List[str] = Field(default_factory=list, description="Client IDs in the household")
    risk_profile: Optional[str] = Field(None, description="Conservative | Moderate | Aggressive")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Household preferences and settings")


class Client(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    household_id: Optional[str] = Field(None, description="Related household ID")
    date_of_birth: Optional[str] = Field(None, description="YYYY-MM-DD")
    ssn_last4: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    kyc_status: Literal["pending", "approved", "rejected"] = "pending"


class Account(BaseModel):
    client_id: str = Field(..., description="Owner client ID")
    household_id: Optional[str] = None
    account_type: Literal["taxable", "ira", "roth_ira", "401k", "529", "trust", "other"]
    custodian: Optional[str] = None
    account_number_masked: Optional[str] = Field(None, description="Masked number for UI")
    balance: float = 0.0
    holdings: List[Dict[str, Any]] = Field(default_factory=list, description="Positions with ticker, weight, cost_basis, etc.")


class Note(BaseModel):
    author_id: str = Field(..., description="Advisor/Staff ID")
    subject: str
    content: str
    client_id: Optional[str] = None
    household_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    visibility: Literal["internal", "shared_with_client"] = "internal"


class Task(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    related_client_id: Optional[str] = None
    related_household_id: Optional[str] = None
    status: Literal["todo", "in_progress", "done", "blocked"] = "todo"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    due_date: Optional[str] = None


class Communication(BaseModel):
    channel: Literal["secure_message", "email", "call", "meeting"]
    direction: Literal["inbound", "outbound"]
    actor_id: Optional[str] = None
    client_id: Optional[str] = None
    household_id: Optional[str] = None
    subject: Optional[str] = None
    content: str
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class Document(BaseModel):
    title: str
    description: Optional[str] = None
    owner_client_id: Optional[str] = None
    household_id: Optional[str] = None
    storage_url: str
    category: Literal["statement", "tax", "estate", "ips", "other"] = "other"
    shared_with_client: bool = False


class Recommendation(BaseModel):
    category: Literal["tax", "investment", "risk", "estate", "communication"]
    title: str
    rationale: str
    impact_score: float = Field(0.0, description="0-1 score of expected benefit")
    client_id: Optional[str] = None
    household_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["proposed", "approved", "implemented", "rejected"] = "proposed"


class Compliance(BaseModel):
    action: str = Field(..., description="What happened (create_note, generate_reco, etc.)")
    actor_id: Optional[str] = None
    resource_type: str = Field(..., description="Entity type affected")
    resource_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    labels: List[str] = Field(default_factory=list)
    severity: Literal["info", "low", "medium", "high"] = "info"
    timestamp: Optional[datetime] = None


# AI analysis request/response payloads
class PortfolioAnalysisRequest(BaseModel):
    household_id: Optional[str] = None
    account_ids: List[str] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    constraints: Dict[str, Any] = Field(default_factory=dict)


class TaxOptimizationRequest(BaseModel):
    household_id: Optional[str] = None
    year: int
    assumptions: Dict[str, Any] = Field(default_factory=dict)


class EstatePlanningRequest(BaseModel):
    household_id: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    facts: Dict[str, Any] = Field(default_factory=dict)


# Minimal user for auth placeholder
class User(BaseModel):
    name: str
    email: str
    is_active: bool = True

