# ChargeShield Evidence Storage & Document Management Service

## Overview

The ChargeShield Evidence Storage Service provides secure, scalable, and audit-compliant evidence document management for chargeback disputes. It combines strict file-type validation, SHA-256 cryptographic integrity hashing, atomic database-filesystem persistence, data-state governance, and granular role-based access control (RBAC).

---

## 1. Storage Architecture & Abstraction

### Current Implementation (Local Filesystem)
Physical evidence files are organized within the configured `EVIDENCE_STORAGE_PATH` (default: `storage/evidence/`). To prevent directory overcrowding and path traversal vulnerabilities, files are organized hierarchically:

```
storage/evidence/
└── {dispute_id}/
    └── {evidence_id}_{safe_filename}
```

- **Physical Storage Key**: Stored as a relative key (e.g., `DSP_000001/EVD_3A9F21B84C10_fulfillment_proof.pdf`).
- **Path Sanitization**: Raw user filenames are sanitized using `os.path.basename`, `pathlib.Path().name`, and regular expression character filtering (`[a-zA-Z0-9_\.-]`).
- **Path Disclosure Prevention**: Internal physical server file paths are never exposed over API response envelopes or logs.

### Object Storage & S3 Migration Path
The `EvidenceStorageService` class (`backend/services/evidence_storage_service.py`) acts as a storage abstraction wrapper. To migrate from local disk to AWS S3, Google Cloud Storage, or MinIO:
1. Replace physical file `open()` and `os.remove()` calls with `boto3` or cloud client calls (`s3_client.upload_fileobj`, `s3_client.generate_presigned_url`).
2. Keep the API contracts and `EvidenceDocumentModel` relational schema completely unchanged.

---

## 2. Supported File Formats & File Size Limits

### Supported Extensions & Content Types
| Format | Extension | Content-Type Header |
| :--- | :--- | :--- |
| **PDF Document** | `.pdf` | `application/pdf` |
| **PNG Image** | `.png` | `image/png` |
| **JPG / JPEG Image** | `.jpg`, `.jpeg` | `image/jpeg` |
| **CSV Document** | `.csv` | `text/csv`, `application/csv` |
| **Text File** | `.txt` | `text/plain` |

### Explicitly Prohibited File Types
Executable files, shell scripts, and system binaries are strictly blocked at upload validation, returning `400 Bad Request`:
- Prohibited: `.exe`, `.sh`, `.py`, `.php`, `.js`, `.bat`, `.cmd`, `.dll`, `.so`, `.bin`, `.vbs`, `.ps1`, `.jar`, `.msi`.

### Maximum Upload Size
- Default Maximum Size: **10 MB** (`10,485,760 bytes`).
- Configurable via `EVIDENCE_MAX_FILE_SIZE_MB` in `.env` / `backend/core/config.py`.

---

## 3. Cryptographic Integrity & Deduplication

### SHA-256 Hashing
Every uploaded file undergoes stream-based SHA-256 hash calculation from raw binary bytes:
$$\text{SHA256}(B) = \text{hex\_digest}$$

### Duplicate Ingestion Handling
When a file is uploaded for a dispute, ChargeShield queries for existing active evidence records matching:
`dispute_id` + `sha256_hash` + `status = 'ACTIVE'`

- **If Duplicate Found**:
  - No duplicate file is written to disk.
  - The existing metadata record is returned with `status: "DUPLICATE_IDEMPOTENT"`.
  - An audit event `EVIDENCE_DUPLICATE_ATTEMPT` is recorded.
  - Prevents storage bloat and accidental file duplication.

---

## 4. Role-Based Access Control (RBAC)

All evidence endpoints strictly enforce server-side RBAC using FastAPI `require_role`:

| Endpoint | Method | Path | Minimum Required Role |
| :--- | :--- | :--- | :--- |
| **Upload Evidence** | `POST` | `/api/v1/cases/{dispute_id}/evidence-upload` | `ADMIN`, `REVIEWER` |
| **List Evidence** | `GET` | `/api/v1/cases/{dispute_id}/evidence` | `ADMIN`, `REVIEWER`, `ANALYST`, `AUDITOR` |
| **Download Evidence** | `GET` | `/api/v1/cases/{dispute_id}/evidence/{evidence_id}` | `ADMIN`, `REVIEWER`, `ANALYST`, `AUDITOR` |
| **Revoke Evidence** | `DELETE` | `/api/v1/cases/{dispute_id}/evidence/{evidence_id}` | `ADMIN` only |

*Note: ANALYST and AUDITOR roles are restricted to read-only access. REVIEWER and ADMIN can upload evidence. Only ADMIN can revoke/soft-delete evidence.*

---

## 5. Data-State Governance

Evidence documents inherit the `data_state` (`PRODUCTION` or `SIMULATION`) directly from their parent dispute case:
- **Production Disputes**: Evidence documents are tagged with `data_state = 'PRODUCTION'`.
- **Simulation Disputes**: Evidence documents are tagged with `data_state = 'SIMULATION'`.
- **Isolation**: Production API queries filter exclusively for `data_state = 'PRODUCTION'`, ensuring synthetic or simulation evidence never contaminates real-world production cases or metrics.

---

## 6. Atomic Storage & Rollback Guarantees

To ensure complete consistency between database metadata and physical storage:
1. **File System First**: Physical file is written to storage.
2. **Database Session Second**: Metadata is added to the SQL transaction and committed.
3. **Compensating Rollback**: If the database transaction fails at commit time:
   - SQL transaction is rolled back (`db.rollback()`).
   - Newly created physical file is immediately removed from disk (`os.remove()`).
   - Prevents orphaned files on disk.

---

## 7. Audit Trail Events

All evidence operations record immutable events via `event_service`:
- `EVIDENCE_UPLOAD`: Published when a document is uploaded successfully.
- `EVIDENCE_VIEW`: Published when an authorized user streams/downloads a document.
- `EVIDENCE_REVOKE`: Published when an Admin revokes an evidence document.
- `EVIDENCE_DUPLICATE_ATTEMPT`: Published when a duplicate file hash is uploaded.
- `EVIDENCE_REJECTED`: Published when a file fails validation (size limit, forbidden extension).

---

## 8. Security Safeguards

1. **Path Traversal Shield**: Strictly verifies that all resolved file paths stay within `os.path.abspath(EVIDENCE_STORAGE_PATH)`.
2. **No Execution Policy**: Uploaded files are saved in non-executable storage directories without execution permissions.
3. **No Direct URL Exposure**: Files are streamed exclusively via `/api/v1/cases/{dispute_id}/evidence/{evidence_id}` with appropriate authentication headers.
