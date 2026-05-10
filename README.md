# Dorm Mail PCU Style

### Dormitory Mail and Lost-Item Management Prototype

Dorm Mail PCU Style is a small campus-operations prototype for managing dormitory mail, parcel pickup, and lost-item handling.

The project focuses on a practical dormitory problem: when parcels or lost items are stored in a shared place, it can be difficult to verify who received what, when it was received, and whether the item is still pending.

This repository is not a production dormitory system.  
It is a pilot-style web prototype for showing how a simple registration, notification, verification, and pickup-log flow can reduce confusion.

---

## Why This Project Exists

Dormitory mail and lost-item handling can create repeated operational problems.

Common issues include:

- unclear pickup ownership
- missing pickup records
- mistaken pickup
- delayed student notification
- difficulty checking long-unclaimed items
- no structured record for later review

This project turns the process into a traceable workflow.

```text
arrival registration
→ student notification
→ PIN / QR pickup code
→ identity check
→ pickup completion log
```

---

## Main Features

### Admin Flow

- register arriving mail or parcel
- input student name / room / carrier / item type
- generate one-time PIN
- generate QR code
- update pickup status
- classify unclaimed items
- check pickup history

### Student Flow

- check arrival notification
- view PIN / QR pickup code
- complete pickup with PIN
- complete pickup with QR
- check pickup status

### Record Flow

- save registration history
- save pickup completion history
- record unclaimed item state
- store processing time and status

---

## System Flow

```text
1. Mail or parcel arrives
2. Admin registers item
3. Student receives or checks arrival notice
4. PIN / QR pickup code is generated
5. Student verifies pickup
6. Pickup completion log is stored
7. Long-unclaimed items are separated for review
```

---

## Screens / Pages

Planned or implemented page types:

- login / role selection
- admin mail registration
- PIN / QR generation result
- student arrival notification
- student pickup code check
- pickup history and logs

---

## Tech Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Frontend

- HTML
- CSS
- Jinja2 Templates

### Data

- SQLite

### Utility

- QR code generation
- pickup status tracking

---

## Repository Structure

```text
Dorm_Mail_Pcu_Style/
├─ README.md
└─ dorm_mail_pcu_style/
   └─ dorm_mail_pcu_style/
      ├─ app/
      │  └─ main.py
      ├─ requirements.txt
      └─ README.md
```

---

## Position in Portfolio

This repository is a supporting campus-service project.

It is smaller than `CityBrain` or `paejae-campus-os-v1`, but it shows a practical approach to campus operations:

| Repository | Role |
|---|---|
| `CityBrain` | cafeteria-centered smart campus MVP |
| `paejae-campus-os-v1` | broader smart campus platform scaffold |
| `Dorm_Mail_Pcu_Style` | small dormitory mail / lost-item workflow prototype |

---

## Current Limits

This project does **not** claim:

- official dormitory deployment
- production-grade authentication
- real student information system integration
- complete privacy review
- production database hardening
- full notification service integration

It is a prototype for workflow design and campus operations thinking.

---

## Future Work

- add login and role-based access control
- add admin audit logs
- add real notification integration
- improve student lookup flow
- add item photo upload
- add long-unclaimed item dashboard
- add privacy and data retention policy
- improve QR/PIN expiration logic

---

## Status

Dorm Mail PCU Style is a campus-operations prototype focused on dormitory mail, parcel pickup, and lost-item workflow management.