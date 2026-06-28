"""Full demo project seed: relational data + document corpus ingestion."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    CommissioningTest,
    Document,
    Project,
    ProjectStatus,
    RFI,
    RFIStatus,
    Specification,
    TestStatus,
)
from app.services.chroma_store import get_chroma_store
from app.services.ingestion import ingest_data_directory

DEMO_PROJECT_NAME = "Mumbai Hyperscale DC-01"

SPECIFICATIONS = [
    {
        "equipment_class": "UPS",
        "requirement_key": "battery_runtime",
        "requirement_text": "UPS battery shall provide minimum 15 minutes runtime at full load for Tier III compliance.",
        "required_value": "15 min",
        "tolerance": None,
        "standard_ref": "Uptime Tier III",
    },
    {
        "equipment_class": "UPS",
        "requirement_key": "efficiency",
        "requirement_text": "UPS system efficiency shall be minimum 96% at 50% load.",
        "required_value": "96%",
        "tolerance": None,
        "standard_ref": "TIA-942",
    },
    {
        "equipment_class": "Chiller",
        "requirement_key": "redundancy",
        "requirement_text": "Cooling plant shall be configured N+2 redundancy for Tier III facility.",
        "required_value": "N+2",
        "tolerance": None,
        "standard_ref": "Uptime Tier III",
    },
    {
        "equipment_class": "Switchgear",
        "requirement_key": "standard",
        "requirement_text": "Medium voltage switchgear shall comply with UL 891.",
        "required_value": "UL 891",
        "tolerance": None,
        "standard_ref": "UL 891",
    },
    {
        "equipment_class": "Generator",
        "requirement_key": "standby_rating",
        "requirement_text": "Standby diesel generator rating shall be 4000 kW minimum.",
        "required_value": "4000 kW",
        "tolerance": None,
        "standard_ref": "Project Spec 26 32 13",
    },
]

RFIS = [
    {
        "number": "RFI-014",
        "subject": "UPS battery runtime clarification",
        "question": "Confirm required UPS battery runtime at full load for Tier III certification.",
        "response": "Minimum 15 minutes at full load per Uptime Tier III and owner specification section 26 33 16.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-022",
        "subject": "Cable tray spacing in electrical room",
        "question": "What is the approved cable tray spacing in main electrical room?",
        "response": "Minimum 300 mm vertical spacing between power and control trays per NFPA 70 and drawing E-102.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-031",
        "subject": "Cable tray spacing — data hall corridor",
        "question": "Cable tray spacing requirement for data hall corridor routing?",
        "response": "Same as RFI-022: 300 mm minimum vertical spacing. Refer to approved response on RFI-022.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-038",
        "subject": "Chiller redundancy configuration",
        "question": "Is N+1 or N+2 required for water-cooled chiller plant?",
        "response": "N+2 redundancy required per Tier III design basis and specification section 23 64 00.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-045",
        "subject": "CO-014 chiller redundancy change",
        "question": "What changed in CO-014 regarding chiller redundancy?",
        "response": "CO-014 upgrades cooling redundancy from N+1 to N+2 and adds one standby chiller unit.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-051",
        "subject": "STS transfer time acceptance",
        "question": "What is the acceptance criteria for static transfer switch transfer time?",
        "response": "Transfer time shall not exceed 4 ms for class 1 STS per Uptime Institute and factory witness test.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-058",
        "subject": "Fire suppression agent in IT whitespace",
        "question": "Approved clean agent for IT whitespace fire suppression?",
        "response": "Novec 1230 per NFPA 2001 and specification section 21 13 00.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-062",
        "subject": "Generator fuel storage capacity",
        "question": "Required on-site diesel storage duration at full load?",
        "response": "72 hours minimum storage at N-1 generator operation per owner requirement.",
        "status": RFIStatus.ANSWERED.value,
    },
    {
        "number": "RFI-071",
        "subject": "Switchgear certification standard",
        "question": "Is IEC 61439 acceptable for medium voltage switchgear submittal?",
        "response": "No. UL 891 is mandatory for this project. IEC submittals are not acceptable.",
        "status": RFIStatus.OPEN.value,
    },
    {
        "number": "RFI-079",
        "subject": "Raised floor grounding grid",
        "question": "Spacing for grounding grid under raised floor tiles?",
        "response": None,
        "status": RFIStatus.OPEN.value,
    },
]

COMMISSIONING_TESTS = [
    {
        "standard_ref": "TIA-942",
        "procedure": "Verify STS transfer time under loaded conditions",
        "system_type": "power",
        "acceptance_criteria": "Transfer time not to exceed 4 ms",
    },
    {
        "standard_ref": "Uptime Tier III",
        "procedure": "UPS battery discharge test at full load",
        "system_type": "power",
        "acceptance_criteria": "Minimum 15 minutes runtime",
    },
    {
        "standard_ref": "TIA-942",
        "procedure": "Generator load bank test — step load acceptance",
        "system_type": "power",
        "acceptance_criteria": "Voltage dip within 15% during step load",
    },
    {
        "standard_ref": "Uptime Tier III",
        "procedure": "Chiller plant failover — single unit loss",
        "system_type": "cooling",
        "acceptance_criteria": "Supply air temperature within 2°C of setpoint within 10 minutes",
    },
    {
        "standard_ref": "TIA-942",
        "procedure": "CRAC unit redundancy failover test",
        "system_type": "cooling",
        "acceptance_criteria": "No hot spot above 27°C in whitespace during failover",
    },
    {
        "standard_ref": "TIA-942",
        "procedure": "Integrated system test — utility loss simulation",
        "system_type": "power",
        "acceptance_criteria": "Zero IT load interruption during planned transfer sequence",
    },
]


def get_or_create_project(db: Session) -> Project:
    project = db.query(Project).filter(Project.name == DEMO_PROJECT_NAME).first()
    if project:
        return project

    project = Project(
        name=DEMO_PROJECT_NAME,
        tier_target="Tier III",
        location="Mumbai, Maharashtra, India",
        status=ProjectStatus.CONSTRUCTION.value,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def seed_structured_data(db: Session, project_id: int) -> dict:
    counts = {"specifications": 0, "rfis": 0, "commissioning_tests": 0}

    for spec in SPECIFICATIONS:
        exists = (
            db.query(Specification)
            .filter(
                Specification.project_id == project_id,
                Specification.equipment_class == spec["equipment_class"],
                Specification.requirement_key == spec["requirement_key"],
            )
            .first()
        )
        if exists:
            continue
        db.add(Specification(project_id=project_id, **spec))
        counts["specifications"] += 1

    for rfi in RFIS:
        exists = db.query(RFI).filter(RFI.project_id == project_id, RFI.number == rfi["number"]).first()
        if exists:
            continue
        db.add(RFI(project_id=project_id, **rfi))
        counts["rfis"] += 1

    for test in COMMISSIONING_TESTS:
        exists = (
            db.query(CommissioningTest)
            .filter(
                CommissioningTest.project_id == project_id,
                CommissioningTest.procedure == test["procedure"],
            )
            .first()
        )
        if exists:
            continue
        db.add(
            CommissioningTest(
                project_id=project_id,
                status=TestStatus.PENDING.value,
                **test,
            )
        )
        counts["commissioning_tests"] += 1

    db.commit()
    return counts


def run_full_seed(db: Session) -> dict:
    project = get_or_create_project(db)
    structured = seed_structured_data(db, project.id)
    ingestion = ingest_data_directory(db, project.id)

    document_count = db.query(Document).filter(Document.project_id == project.id).count()
    vector_count = get_chroma_store().count()

    return {
        "message": "Demo project seeded successfully",
        "project_id": project.id,
        "project_name": project.name,
        "structured": structured,
        "ingestion": ingestion,
        "documents_in_db": document_count,
        "vectors_in_chroma": vector_count,
    }
