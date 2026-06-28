# Commissioning Test: STS Transfer Time
**Standard:** TIA-942  
**System:** Power  
**Procedure ID:** PWR-001

## Procedure
1. Configure STS with nominal load at 40% of rated capacity.
2. Simulate utility loss using test protocol TP-E-101.
3. Capture transfer event with oscilloscope (minimum 1 MHz sampling).
4. Repeat for three consecutive transfers.

## Acceptance Criteria
Transfer time **shall not exceed 4 ms** for Class 1 STS. No interruption to critical IT load.

## Records Required
Oscilloscope traces, event log export, witness sign-off sheet.
