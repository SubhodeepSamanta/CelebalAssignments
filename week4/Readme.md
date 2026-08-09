# Week 4 — Azure Cloud Fundamentals & ADF Data Pipeline

Implementation of an enterprise cloud ETL pipeline using **Azure Data Factory (ADF)** and **Azure Blob Storage** for ingestion and transfer of the Superstore dataset.

---

## Assignment Contents & Screenshots

| Screenshot / File | Target Task | Pipeline Activity & Description |
|---|---|---|
| [`01-resource-group.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/01-resource-group.png) | Task 1 | Created Azure Resource Group `rg-superstore-pipeline` in Malaysia West region |
| [`02-storage-container.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/02-storage-container.png) | Task 2 | Storage Account `stsuperstoreadf` & Blob Container `superstore-container` created with uploaded CSV |
| [`03-adf-overview.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/03-adf-overview.png) | Task 3 | Provisioned Azure Data Factory instance `adf-superstore-pipelineSS` |
| [`04-linked-service.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/04-linked-service.png) | Task 3 | Linked Service `ls_blob_superstore` established with successful connection test |
| [`05-datasets.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/05-datasets.png) | Task 3 | Source dataset `ds_superstore_source` & Sink dataset `ds_superstore_destination` configured |
| [`06-get-metadata.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/06-get-metadata.png) | Task 3 | `Get Metadata` activity configured to inspect file size and row existence |
| [`07-pipeline-design.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/07-pipeline-design.png) | Task 4 | `Copy Data` activity pipeline design (`pl_copy_superstore_data`) |
| [`08-pipeline-succeeded.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/08-pipeline-succeeded.png) | Task 5 | Successful execution status for the data copying run |
| [`09-iam-roles.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/09-iam-roles.png) | Task 6 | IAM Role assignments (`Reader`, `Contributor`, `Storage Blob Data Contributor`) |
| [`10-mini-project-combined.png`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/ScreenShots/10-mini-project-combined.png) | Mini-Project | Chained **Get Metadata → Copy Data** end-to-end pipeline in a single successful Debug run |
| [`Week4_Assignment4_Report.pdf`](file:///c:/Users/USER/Desktop/CelebalAssignments/week4/Report/Week4_Assignment4_Report.pdf) | Deliverable | Full written technical report with step-by-step documentation and embedded screenshots |

---

## Azure Infrastructure Configuration

- **Resource Group**: `rg-superstore-pipeline`
- **Storage Account**: `stsuperstoreadf`
- **Blob Container**: `superstore-container`
- **Azure Data Factory**: `adf-superstore-pipelineSS`
- **Linked Service**: `ls_blob_superstore`
- **Source Dataset**: `ds_superstore_source` (DelimitedText)
- **Destination Dataset**: `ds_superstore_destination` (DelimitedText)
- **Pipelines**: `pl_get_metadata_check`, `pl_copy_superstore_data`
- **Deployment Region**: Malaysia West

---

## Technical Notes & Resolved Engineering Issues

1. **Destination Dataset Schema Import (404 Blob Missing)**:
   - *Issue*: Initial setup threw a missing blob error during schema import because the sink file did not yet exist.
   - *Resolution*: Configured `Import schema` to `None` on `ds_superstore_destination`, permitting dynamic output creation upon execution.
2. **`DelimitedTextMoreColumnsThanDefined` Exception**:
   - *Issue*: Unescaped commas in text fields within row 34 caused column misalignment during strict schema mapping.
   - *Resolution*: Removed fixed column index mapping from the `Copy Data` activity, enabling dynamic runtime column resolution and quotation handling.

---

## Pipeline Execution Flow

```
[Trigger / Debug Run] 
        │
        ▼
┌──────────────────────────────┐
│  Get Metadata Activity       │
│  (Validates blob presence)   │
└──────────────┬───────────────┘
               │ On Success
               ▼
┌──────────────────────────────┐
│  Copy Data Activity          │
│  (Transfers CSV to sink)     │
└──────────────────────────────┘
```