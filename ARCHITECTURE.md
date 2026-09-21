# Technical Architecture & Deployment Framework
## VisionX • Legal Metrology (Packaged Commodities) Compliance Enforcement System

---

### 1. Executive Summary
**VisionX** is an enterprise-grade automated regulatory compliance surveillance and enforcement system designed for Legal Metrology officers under the Ministry of Consumer Affairs, Government of India. The platform audits packaged commodity labels against mandatory statutory declarations prescribed under the **Legal Metrology (Packaged Commodities) Rules, 2011**, using a 5-stage hybrid computer vision and NLP pipeline, an asynchronous job processing engine, a declarative statutory rule evaluation engine, and an automated evidentiary legal dossier generator.

---

### 2. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER (SPA)                              │
│  React 18 + Vite + TypeScript + Tailwind CSS + Lucide Icons + Recharts          │
│  • Role-Based Access Control (Admin / Inspector / Viewer)                       │
│  • Mobile-First Responsive Drawer Navigation & Multilingual Interface (10 Indic)│
│  • Direct HTML5 Native Device Camera Stream (facingMode: environment)           │
│  • Interactive Bounding Box Canvas (Hover Tooltips, Click-to-Checklist Sync)    │
│  • Asynchronous Multi-Stage Progress Bar (Polling /products/scan/{id}/status)   │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ HTTPS / REST (JSON + Multipart)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY / UNIFIED BACKEND                         │
│  FastAPI (Python 3.11) + Uvicorn + Pydantic v2 + OAuth2 / JWT (HS256)           │
│  • REST Routing: /auth, /products, /reports, /dashboard, /admin, /storage        │
│  • Session Management: SQLAlchemy 2.0 ORM with Connection Pooling               │
│  • Dual Persistence Profile: PostgreSQL 16 (Enterprise) / SQLite (Standalone)   │
│  • Lifespan Handlers: Schema Verification, Rule Hydration, Zero-Config Seeding  │
│  • Static File Mounting: Directly serves compiled React SPA from /frontend/dist │
└──────────────────┬─────────────────────┬───────────────────┬────────────────────┘
                   │                     │                   │
         Postgres  │           Redis Msg │         Storage   │ S3 Put/Get
         Session   ▼           Broker    ▼         Fallback  ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────────┐
│    DATA PERSISTENCE  │  │  MESSAGE BROKER      │  │  OBJECT STORAGE             │
│ PostgreSQL 16 /      │  │  Redis 7.0 In-Memory │  │  MinIO S3-Compatible        │
│ SQLite Local Engine  │  │  • Celery Task Queue │  │  • Scanned Label Images     │
│ • Users, Products    │  │  • In-Process Worker │  │  • ReportLab / WeasyPrint   │
│ • ScanJobs, Rules    │  │    Fallback (Dev)    │  │  • python-docx Reports      │
│ • Audit Trails       │  │  • Progress Channel  │  │  • Seized Photo Evidence    │
└──────────────────────┘  └──────────┬───────────┘  └─────────────────────────────┘
                                     │ Task Dispatch
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      5-STAGE HYBRID COMPUTER VISION PIPELINE                    │
│  Asynchronous Pipeline (Celery Worker or Background Task Queue)                 │
│                                                                                 │
│  STAGE A: Image Preprocessing (OpenCV 4.9 Headless)                             │
│  ├── Deskewing: Hough Line Transform & minAreaRect angle compensation           │
│  ├── Contrast Equalization: CLAHE on CIE-LAB L-channel (anti-glare & foil sheen)│
│  ├── Denoising: Bilateral Filter (edge-preserving smoothing)                    │
│  └── Upscaling: Bicubic Laplacian Sharpening for micro-font declaration text    │
│                                                                                 │
│  STAGE B: Multi-Engine OCR & Spatial Reconciliation                             │
│  ├── Primary: PaddleOCR (rotated text detection & DBNet layout)                 │
│  ├── Secondary: Tesseract (PSM 6 & 11 fallback)                                 │
│  └── Reconciliation: Spatial IoU overlap matching, Levenshtein distance check,  │
│      and joint confidence scoring. Conflicting tokens flagged as "needs_review".│
│                                                                                 │
│  STAGE C: Spatial Layout Clustering                                             │
│  └── 2D Bounding Box Proximity: Agglomerates scattered word tokens into         │
│      coherent declaration blocks (e.g. multi-line manufacturer address).        │
│                                                                                 │
│  STAGE D: Semantic Field Extraction & Cross-Validation                          │
│  ├── LLM Mapping: Claude/Gemini API via strict JSON Schema prompt               │
│  ├── Deterministic Fallback: High-speed heuristic NER parser                    │
│  └── Sanity Cross-Validator: Regex checks against mandatory statutory phrases    │
│      ("inclusive of all taxes"), metric units, dates, and consumer contacts.    │
│                                                                                 │
│  STAGE E: Physical Font Scale & Readability Checker                             │
│  └── Scale Ratio: (pixels_per_mm = img_w / ref_scale_mm). Computes physical     │
│      character height in mm vs Second Schedule minimum height thresholds.       │
│                                                                                 │
│  STAGE F: Legal Metrology (2011 Rules) Rule Engine                              │
│  └── Declarative rule evaluation: Rule 6(1)(a)-(f), Rule 7, Rule 13             │
│      Outputs Pass/Fail/Review verdict, compliance score, and legal grounds.     │
│                                                                                 │
│  STAGE G: Dual Evidentiary Report Generation                                    │
│  ├── Vector PDF: ReportLab pure-Python engine (zero OS dependencies) with       │
│  │   official emblem, QR verification badge, and officer signature block        │
│  └── DOCX: Editable inspection notice created via python-docx                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Pipeline Data Flow & State Machine

The inspection scan lifecycle executes asynchronously across a deterministic state machine:

$$\text{PENDING} \xrightarrow{15\%} \text{PREPROCESSING} \xrightarrow{38\%} \text{OCR\_RUNNING} \xrightarrow{65\%} \text{EXTRACTING} \xrightarrow{88\%} \text{EVALUATING} \xrightarrow{100\%} \text{COMPLETED}$$

1. **Upload & Enqueue**:
   - Inspector captures a live photo via HTML5 native camera or uploads an image file (front/back label, optional scale).
   - Backend persists image into storage and generates a UUIDv4 `ScanJob`.
   - Dispatches background task `process_scan_task(job_id)`.
2. **Progress Polling**:
   - The React frontend polls `GET /api/v1/products/scan/{job_id}/status` every 750ms.
   - The UI displays live animated progress bars with granular status strings (`Stage A: OpenCV deskew...`, `Stage B: OCR reconciliation...`).
3. **Reconciliation & Semantic Validation**:
   - Overlapping tokens with IoU $\ge 0.25$ and string similarity $\ge 0.70$ are reconciled to the highest confidence score.
   - Disagreeing tokens are flagged with `needs_review: true`.
   - Extracted fields are cross-validated against strict regular expressions:
     - MRP format requires numerical amount and mandatory phrase `"inclusive of all taxes"`.
     - Net quantity must use international metric units (`g`, `kg`, `ml`, `L`, `N`). Illegal units (`gms`, `kgs`) trigger an explicit statutory violation under Rule 13.
4. **Evidentiary Legal Dossier**:
   - Structured JSON output feeds both the pure-Python **ReportLab** PDF generator and the **python-docx** Word generator, guaranteeing zero drift between report formats and 100% platform portability across Windows, Linux, and Cloud environments.

---

### 4. Containerization & Deployment Framework

#### Production Enterprise Mode (Docker Compose):
| Service | Image / Base | Internal Port | Exposed Port | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `postgres` | `postgres:16-alpine` | `5432` | `5432` | Primary relational database with healthcheck. |
| `redis` | `redis:7-alpine` | `6379` | `6379` | Celery message broker and result backend. |
| `minio` | `minio/minio:latest` | `9000`, `9001` | `9000`, `9001` | S3-compatible blob storage with console UI. |
| `backend` | `python:3.11-slim` | `8000` | `8000` | FastAPI REST server with OpenCV, ReportLab, Tesseract. |
| `worker` | `python:3.11-slim` | — | — | Celery worker executing multi-stage OCR pipeline. |
| `frontend` | `node:20-alpine` $\to$ `nginx:alpine` | `80` | `5173` | Multi-stage production build served via Nginx. |

#### Standalone Zero-Config Mode (Instant Hackathon Demo):
- **Command**: `python run_server.py` or double-click `start.bat`.
- **Architecture**: Single process running FastAPI on port `8080`, SQLite embedded database (`legalmetro.db`), in-process background worker, and pre-built React SPA static asset mounting.
- **LAN Discovery**: Automatically detects host Wi-Fi adapter IP and displays mobile URL for instant smartphone testing.

---

### 5. Security & Statutory Governance
- **Role-Based Access Control (RBAC)**: Fine-grained scopes for `admin` (rule configuration, user management), `inspector` (scan, annotate, report generation), and `viewer` (read-only audit surveillance).
- **Statutory Evidentiary Chain**: Every inspection record stores the inspecting officer's ID, badge number, timestamp, raw OCR tokens with bounding boxes, extracted declarations, and generated report links for legal evidentiary proceedings under Section 18 of the Legal Metrology Act, 2009.
- **Fail-Safe Fallbacks**: Zero external dependency lock-in. If cloud LLM APIs or S3 clusters are unreachable, the system automatically falls back to local high-fidelity heuristic NER parsers and local disk storage with full UI integrity.
