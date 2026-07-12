# Week 4 - Assignment 4: Azure Cloud Fundamentals & ADF Pipeline

This folder contains the screenshots taken while completing the assignment, along with the full
written report (PDF).

## Contents

| File | Task | Description |
|------|------|-------------|
| `01-resource-group.png` | Task 1 | Resource group `rg-superstore-pipeline` created (Malaysia West) |
| `02-storage-container.png` | Task 2 | Blob container `superstore-container` with uploaded Superstore CSV |
| `03-adf-overview.png` | Task 3 | Data Factory `adf-superstore-pipelineSS` - Overview page |
| `04-linked-service.png` | Task 3 | Linked service `ls_blob_superstore` - successful test connection |
| `05-datasets.png` | Task 3 | Source & destination datasets (`ds_superstore_source`, `ds_superstore_destination`) |
| `06-get-metadata.png` | Task 3 | Get Metadata activity - debug run succeeded |
| `07-pipeline-design.png` | Task 4 | Copy Data pipeline design (`pl_copy_superstore_data`) |
| `08-pipeline-succeeded.png` | Task 5 | Pipeline execution result - status Succeeded |
| `09-iam-roles.png` | Task 6 | IAM role assignments (Reader, Contributor, Storage Blob Data Contributor) |
| `Week4_Assignment4_Report.pdf` | All | Full written report with explanations + embedded screenshots |

## Resource naming used in this assignment

- Resource Group: `rg-superstore-pipeline`
- Storage Account: `stsuperstoreadf`
- Blob Container: `superstore-container`
- Data Factory: `adf-superstore-pipelineSS`
- Linked Service: `ls_blob_superstore`
- Datasets: `ds_superstore_source`, `ds_superstore_destination`
- Pipelines: `pl_get_metadata_check`, `pl_copy_superstore_data`
- Region: Malaysia West
- Source dataset: Sample Superstore dataset (Kaggle)

## Notes / issues encountered

- **Destination dataset schema import error (404 - Blob missing):** happened because the output file
  doesn't exist until the pipeline actually runs. Fixed by setting Import schema to `None` for the
  destination dataset.
- **`DelimitedTextMoreColumnsThanDefined` on Copy Data run:** row 34 of the source CSV had a comma
  inside a text field that wasn't properly quote-wrapped, causing an extra column to be detected.
  Fixed by clearing the fixed column mapping on the Copy activity so columns map dynamically at runtime.

See the PDF report for the full write-up of each task.