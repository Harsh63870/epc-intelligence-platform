"""Specification compliance checking for vendor submittals."""
from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models import AuditEvent, NCSeverity, NCStatus, NonConformance, Specification, Submittal
from app.services.groq_client import GroqError, chat_completion, parse_json_response

SEVERITY_BY_KEY = {
    "battery_runtime": NCSeverity.CRITICAL.value,
    "standard": NCSeverity.CRITICAL.value,
    "redundancy": NCSeverity.MAJOR.value,
    "standby_rating": NCSeverity.MAJOR.value,
    "efficiency": NCSeverity.MINOR.value,
}


def extract_attributes(text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}

    class_match = re.search(r"## Equipment Class\s*\n\s*(\w+)", text, re.IGNORECASE)
    if class_match:
        attrs["equipment_class"] = class_match.group(1).strip()

    table_rows = re.findall(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", text)
    for key, val in table_rows:
        key = key.strip().lower()
        val = val.strip()
        if key in {"parameter", "submitted value", "---", "-----------"}:
            continue
        normalized = _normalize_key(key)
        attrs[normalized] = val

    return attrs


def _normalize_key(key: str) -> str:
    mapping = {
        "battery runtime (full load)": "battery_runtime",
        "battery runtime": "battery_runtime",
        "configuration": "redundancy",
        "standby rating": "standby_rating",
        "standard": "standard",
        "efficiency at 50% load": "efficiency",
        "efficiency": "efficiency",
    }
    return mapping.get(key.lower(), key.lower().replace(" ", "_"))


def _extract_numeric(value: str) -> float | None:
    match = re.search(r"[\d.]+", value.replace(",", ""))
    return float(match.group()) if match else None


def _values_match(required: str, submitted: str, requirement_key: str) -> bool:
    req = required.lower().strip()
    sub = submitted.lower().strip()

    if req in sub or sub in req:
        return True

    if requirement_key == "redundancy":
        return _redundancy_meets(req, sub)

    req_num = _extract_numeric(req)
    sub_num = _extract_numeric(sub)
    if req_num is not None and sub_num is not None:
        if requirement_key == "battery_runtime":
            return sub_num >= req_num
        if requirement_key in {"standby_rating", "efficiency"}:
            return sub_num >= req_num

    if requirement_key == "standard":
        return req.replace(" ", "") in sub.replace(" ", "")

    return req == sub


def _redundancy_meets(required: str, submitted: str) -> bool:
    order = {"n+0": 0, "n+1": 1, "n+2": 2, "n+3": 3}
    req_level = next((v for k, v in order.items() if k in required.replace(" ", "").lower()), 0)
    sub_level = next((v for k, v in order.items() if k in submitted.replace(" ", "").lower()), 0)
    return sub_level >= req_level


def _groq_extract_attributes(text: str) -> dict[str, str] | None:
    try:
        raw = chat_completion(
            system="Extract equipment submittal attributes as JSON. Keys: equipment_class, battery_runtime, redundancy, standard, standby_rating, efficiency. Use submitted values only.",
            user=text[:4000],
            json_mode=True,
        )
        data = parse_json_response(raw)
        return {str(k): str(v) for k, v in data.items()}
    except GroqError:
        return None


def check_submittal_compliance(
    db: Session,
    *,
    project_id: int,
    vendor: str,
    text: str,
    filename: str,
    submittal_id: int | None = None,
) -> dict:
    attrs = extract_attributes(text)
    groq_attrs = _groq_extract_attributes(text)
    if groq_attrs:
        attrs.update({k: v for k, v in groq_attrs.items() if v})

    equipment_class = attrs.get("equipment_class", "Unknown")
    specs = (
        db.query(Specification)
        .filter(Specification.project_id == project_id, Specification.equipment_class == equipment_class)
        .all()
    )

    if submittal_id is None:
        submittal = Submittal(
            project_id=project_id,
            vendor=vendor,
            equipment_class=equipment_class,
            parsed_attributes=attrs,
            status="reviewed",
        )
        db.add(submittal)
        db.commit()
        db.refresh(submittal)
    else:
        submittal = db.query(Submittal).filter(Submittal.id == submittal_id).first()
        if not submittal:
            raise ValueError("Submittal not found")
        submittal.parsed_attributes = attrs
        db.commit()

    existing_ncs = db.query(NonConformance).filter(NonConformance.submittal_id == submittal.id).all()
    for nc in existing_ncs:
        db.delete(nc)
    db.commit()

    checks: list[dict] = []
    ncs_created: list[NonConformance] = []

    for spec in specs:
        submitted_val = attrs.get(spec.requirement_key, "Not provided")
        required_val = spec.required_value or spec.requirement_text
        conforms = _values_match(required_val or "", submitted_val, spec.requirement_key)

        check = {
            "spec_id": spec.id,
            "requirement_key": spec.requirement_key,
            "requirement_text": spec.requirement_text,
            "required_value": required_val,
            "submitted_value": submitted_val,
            "standard_ref": spec.standard_ref,
            "status": "pass" if conforms else "fail",
        }
        checks.append(check)

        if not conforms:
            severity = SEVERITY_BY_KEY.get(spec.requirement_key, NCSeverity.MAJOR.value)
            deviation = (
                f"Submitted '{submitted_val}' does not meet required '{required_val}' "
                f"for {spec.requirement_key} ({spec.standard_ref or 'project spec'})"
            )
            nc = NonConformance(
                submittal_id=submittal.id,
                spec_id=spec.id,
                severity=severity,
                deviation=deviation,
                status=NCStatus.OPEN.value,
            )
            db.add(nc)
            ncs_created.append(nc)

    db.add(
        AuditEvent(
            project_id=project_id,
            entity_type="submittal",
            entity_id=submittal.id,
            action=f"Compliance check on {filename}: {len(ncs_created)} NC(s) flagged",
            actor="spec_compliance_agent",
            metadata_json={"filename": filename, "nc_count": len(ncs_created)},
        )
    )
    db.commit()

    for nc in ncs_created:
        db.refresh(nc)

    return {
        "submittal_id": submittal.id,
        "vendor": vendor,
        "equipment_class": equipment_class,
        "filename": filename,
        "parsed_attributes": attrs,
        "checks": checks,
        "non_conformances": [
            {
                "id": nc.id,
                "spec_id": nc.spec_id,
                "severity": nc.severity,
                "deviation": nc.deviation,
                "status": nc.status,
            }
            for nc in ncs_created
        ],
        "passed": sum(1 for c in checks if c["status"] == "pass"),
        "failed": sum(1 for c in checks if c["status"] == "fail"),
    }
