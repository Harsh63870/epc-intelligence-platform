# UPS System Specification — 500 kVA
**Project:** Mumbai Hyperscale DC-01  
**Section:** 26 33 16  
**Standard:** Uptime Tier III, TIA-942

## 1. General
Provide static UPS system rated 500 kVA, parallel redundant configuration, suitable for Tier III data centre application.

## 2. Performance Requirements
- **Battery runtime:** Minimum **15 minutes** at full rated load (500 kVA) without utility power.
- **Efficiency:** Minimum **96%** at 50% load, measured per IEC 62040-3.
- **Output voltage regulation:** ±1% under steady-state conditions.
- **Total harmonic distortion (THD):** Less than 3% at linear load.

## 3. Battery System
Valve-regulated lead-acid or approved lithium-ion battery system. Battery capacity shall be calculated to support 15-minute runtime at end-of-life (EOL) degradation factor of 0.85.

## 4. Monitoring
UPS shall provide SNMP, Modbus, and dry-contact alarms for battery low, overload, and bypass status.

## 5. Witness Testing
Factory and site witness tests required. Battery discharge test mandatory prior to handover.
