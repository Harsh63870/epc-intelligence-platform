"""SQLAlchemy models for EPC Intelligence Platform."""
import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    CONSTRUCTION = "construction"
    COMMISSIONING = "commissioning"
    COMPLETE = "complete"


class DocumentType(str, enum.Enum):
    SPECIFICATION = "specification"
    SUBMITTAL = "submittal"
    RFI = "rfi"
    CHANGE_ORDER = "change_order"
    MEETING_MINUTES = "meeting_minutes"
    COMMISSIONING = "commissioning"
    OTHER = "other"


class NCSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class NCStatus(str, enum.Enum):
    OPEN = "open"
    WAIVED = "waived"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    CLOSED = "closed"


class RFIStatus(str, enum.Enum):
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"


class ShipmentStatus(str, enum.Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    DELAYED = "delayed"
    DELIVERED = "delivered"


class TestStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NC = "nc"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier_target: Mapped[str] = mapped_column(String(50), default="Tier III")
    location: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(50), default=ProjectStatus.PLANNING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="project")
    specifications: Mapped[list["Specification"]] = relationship(back_populates="project")
    submittals: Mapped[list["Submittal"]] = relationship(back_populates="project")
    rfis: Mapped[list["RFI"]] = relationship(back_populates="project")
    schedule_tasks: Mapped[list["ScheduleTask"]] = relationship(back_populates="project")
    procurement_items: Mapped[list["ProcurementItem"]] = relationship(back_populates="project")
    commissioning_tests: Mapped[list["CommissioningTest"]] = relationship(back_populates="project")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), default=DocumentType.OTHER.value)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="documents")


class Specification(Base):
    __tablename__ = "specifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    equipment_class: Mapped[str] = mapped_column(String(100), nullable=False)
    requirement_key: Mapped[str] = mapped_column(String(255), nullable=False)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    required_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tolerance: Mapped[str | None] = mapped_column(String(255), nullable=True)
    standard_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_doc_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="specifications")


class Submittal(Base):
    __tablename__ = "submittals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    equipment_class: Mapped[str] = mapped_column(String(100), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    parsed_attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="submittals")
    non_conformances: Mapped[list["NonConformance"]] = relationship(back_populates="submittal")


class NonConformance(Base):
    __tablename__ = "non_conformances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submittal_id: Mapped[int] = mapped_column(ForeignKey("submittals.id"), nullable=False)
    spec_id: Mapped[int | None] = mapped_column(ForeignKey("specifications.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default=NCSeverity.MAJOR.value)
    deviation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=NCStatus.OPEN.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submittal: Mapped["Submittal"] = relationship(back_populates="non_conformances")


class RFI(Base):
    __tablename__ = "rfis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=RFIStatus.OPEN.value)
    similar_rfi_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="rfis")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ScheduleTask(Base):
    __tablename__ = "schedule_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    planned_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planned")
    critical_path: Mapped[bool] = mapped_column(Boolean, default=False)
    depends_on_procurement_id: Mapped[int | None] = mapped_column(ForeignKey("procurement_items.id"), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    project: Mapped["Project"] = relationship(back_populates="schedule_tasks")


class ProcurementItem(Base):
    __tablename__ = "procurement_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier: Mapped[str] = mapped_column(String(255), nullable=False)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=ShipmentStatus.ON_TRACK.value)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    origin_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    dest_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dest_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="procurement_items")


class CommissioningTest(Base):
    __tablename__ = "commissioning_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    standard_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    procedure: Mapped[str] = mapped_column(Text, nullable=False)
    system_type: Mapped[str] = mapped_column(String(50), default="power")
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=TestStatus.PENDING.value)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="commissioning_tests")
