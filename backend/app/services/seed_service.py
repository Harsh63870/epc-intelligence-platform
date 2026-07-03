"""Full demo project seed: relational data + document corpus ingestion."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import (
    CommissioningTest,
    Document,
    ProcurementItem,
    Project,
    ProjectStatus,
    RFI,
    RFIStatus,
    ScheduleTask,
    ShipmentStatus,
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


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def seed_operations_data(db: Session, project_id: int) -> dict:
    """Seed procurement items and schedule tasks with realistic risk scenarios."""
    counts = {"procurement_items": 0, "schedule_tasks": 0}

    now = _utcnow()
    mumbai_lat, mumbai_lng = 19.0760, 72.8777

    procurement_defs = [
        {
            "equipment_type": "UPS 500kVA",
            "supplier": "PowerTech Systems",
            "eta": now + timedelta(days=18),
            "status": ShipmentStatus.ON_TRACK.value,
            "risk_score": 0.1,
            "origin_lat": 48.8566,
            "origin_lng": 2.3522,
            "current_lat": 35.0,
            "current_lng": 45.0,
        },
        {
            "equipment_type": "Generator 4000kW",
            "supplier": "DieselPower GmbH",
            "eta": now + timedelta(days=35),
            "status": ShipmentStatus.DELAYED.value,
            "risk_score": 0.85,
            "origin_lat": 51.1657,
            "origin_lng": 10.4515,
            "current_lat": 25.0,
            "current_lng": 55.0,
        },
        {
            "equipment_type": "MV Switchgear",
            "supplier": "GridEquip Inc",
            "eta": now + timedelta(days=22),
            "status": ShipmentStatus.AT_RISK.value,
            "risk_score": 0.55,
            "origin_lat": 40.7128,
            "origin_lng": -74.0060,
            "current_lat": 30.0,
            "current_lng": 35.0,
        },
        {
            "equipment_type": "Water-Cooled Chillers (N+2)",
            "supplier": "CoolFlow Asia",
            "eta": now + timedelta(days=28),
            "status": ShipmentStatus.ON_TRACK.value,
            "risk_score": 0.15,
            "origin_lat": 31.2304,
            "origin_lng": 121.4737,
            "current_lat": 20.0,
            "current_lng": 90.0,
        },
        {
            "equipment_type": "Static Transfer Switches",
            "supplier": "TransferTech",
            "eta": now + timedelta(days=12),
            "status": ShipmentStatus.ON_TRACK.value,
            "risk_score": 0.05,
            "origin_lat": 37.7749,
            "origin_lng": -122.4194,
            "current_lat": 15.0,
            "current_lng": 65.0,
        },
    ]

    proc_map: dict[str, ProcurementItem] = {}
    for pdef in procurement_defs:
        existing = (
            db.query(ProcurementItem)
            .filter(
                ProcurementItem.project_id == project_id,
                ProcurementItem.equipment_type == pdef["equipment_type"],
            )
            .first()
        )
        if existing:
            proc_map[pdef["equipment_type"]] = existing
            continue
        item = ProcurementItem(
            project_id=project_id,
            dest_lat=mumbai_lat,
            dest_lng=mumbai_lng,
            **pdef,
        )
        db.add(item)
        db.flush()
        proc_map[pdef["equipment_type"]] = item
        counts["procurement_items"] += 1

    task_defs = [
        {
            "name": "Electrical room fit-out — UPS installation",
            "planned_start": now + timedelta(days=20),
            "planned_end": now + timedelta(days=35),
            "critical_path": True,
            "proc_key": "UPS 500kVA",
        },
        {
            "name": "Generator yard civil works and fuel system",
            "planned_start": now + timedelta(days=25),
            "planned_end": now + timedelta(days=45),
            "critical_path": True,
            "proc_key": "Generator 4000kW",
        },
        {
            "name": "MV switchgear energization",
            "planned_start": now + timedelta(days=18),
            "planned_end": now + timedelta(days=28),
            "critical_path": True,
            "proc_key": "MV Switchgear",
        },
        {
            "name": "Chiller plant installation and piping",
            "planned_start": now + timedelta(days=30),
            "planned_end": now + timedelta(days=50),
            "critical_path": True,
            "proc_key": "Water-Cooled Chillers (N+2)",
        },
        {
            "name": "STS commissioning and load bank test",
            "planned_start": now + timedelta(days=14),
            "planned_end": now + timedelta(days=20),
            "critical_path": True,
            "proc_key": "Static Transfer Switches",
        },
        {
            "name": "Raised floor and containment install",
            "planned_start": now + timedelta(days=10),
            "planned_end": now + timedelta(days=25),
            "critical_path": False,
            "proc_key": None,
        },
        {
            "name": "Integrated system test (IST)",
            "planned_start": now + timedelta(days=55),
            "planned_end": now + timedelta(days=65),
            "critical_path": True,
            "proc_key": "Generator 4000kW",
        },
    ]

    for tdef in task_defs:
        exists = (
            db.query(ScheduleTask)
            .filter(ScheduleTask.project_id == project_id, ScheduleTask.name == tdef["name"])
            .first()
        )
        if exists:
            continue
        proc_id = proc_map[tdef["proc_key"]].id if tdef["proc_key"] else None
        db.add(
            ScheduleTask(
                project_id=project_id,
                name=tdef["name"],
                planned_start=tdef["planned_start"],
                planned_end=tdef["planned_end"],
                critical_path=tdef["critical_path"],
                depends_on_procurement_id=proc_id,
                status="planned",
            )
        )
        counts["schedule_tasks"] += 1

    db.commit()
    return counts


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
    operations = seed_operations_data(db, project.id)
    structured.update(operations)
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
