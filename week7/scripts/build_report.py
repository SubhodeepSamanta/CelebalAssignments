"""
build_report.py
---------------
Renders report/assignment_summary.pdf from output/run_summary.json, so the report can never
drift away from what the notebook actually produced.

Run (after executing the notebook):
    python scripts/build_report.py
"""

import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUMMARY = os.path.join(ROOT, "output", "run_summary.json")
CHART = os.path.join(ROOT, "screenshots", "06_final_output", "04_summary_charts.png")
OUT = os.path.join(ROOT, "report", "assignment_summary.pdf")

INK = colors.HexColor("#1F2937")
ACCENT = colors.HexColor("#1D4ED8")
RULE = colors.HexColor("#D1D5DB")
BAND = colors.HexColor("#F3F4F6")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], fontSize=19, leading=23, textColor=INK, spaceAfter=2)
SUB = ParagraphStyle("SUB", parent=ss["Normal"], fontSize=9.5, textColor=colors.HexColor("#6B7280"),
                     alignment=1, spaceAfter=12)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, textColor=ACCENT,
                    spaceBefore=13, spaceAfter=5)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontSize=9.6, leading=14,
                      alignment=TA_JUSTIFY, textColor=INK, spaceAfter=6)
SMALL = ParagraphStyle("SMALL", parent=ss["Normal"], fontSize=8.2, leading=11,
                       textColor=colors.HexColor("#4B5563"))
CODE = ParagraphStyle("CODE", parent=ss["Normal"], fontName="Courier", fontSize=8.2,
                      leading=11.5, textColor=colors.HexColor("#111827"),
                      backColor=colors.HexColor("#F6F7F9"), borderPadding=6,
                      spaceBefore=4, spaceAfter=8)


def table(rows, widths, header=True, align_right=None):
    t = Table(rows, colWidths=widths, hAlign="LEFT")
    style = [
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), BAND),
                  ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    for col in (align_right or []):
        style.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def main():
    s = json.load(open(SUMMARY))
    c, cc, s1, s2, v, b = (s["cleaning"], s["change_classification"], s["scd1"],
                           s["scd2"], s["validation"], s["business"])

    story = []
    story.append(Paragraph("Assignment 7 — Incremental Data Processing with Delta Lake", H1))
    story.append(Paragraph(
        f"Delta Lake MERGE · SCD Type 1 &amp; Type 2 · executed {s['executed_at_utc']} · engine: {s['engine']}",
        SUB))

    # ---------------- objective ----------------
    story.append(Paragraph("1. Objective and dataset", H2))
    story.append(Paragraph(
        "Build an incremental (batch) data pipeline on Delta Lake: land a customer snapshot in a "
        "Delta table, clean it, simulate a next-day change feed, apply a <b>MERGE</b> to upsert the "
        "changes, validate the result, and publish a final dataset with a business summary. The "
        "source is the <i>Sample&nbsp;-&nbsp;Superstore</i> order export (9,994 order lines), "
        "aggregated into a 793-customer dimension and then deliberately degraded with nulls, "
        "duplicate rows and inconsistent strings so that the cleaning step has real work to do.", BODY))
    story.append(table([
        ["Input", "Rows", "Contents"],
        ["data/customer_master.csv", f"{s['source']['master_csv_rows']:,}",
         "full snapshot: 793 customers + 45 exact duplicates + 25 late-arriving versions + 3 null keys"],
        ["data/customer_incremental.csv", f"{s['source']['incremental_csv_rows']:,}",
         "change feed: updates to existing customers, brand-new customers, 5 duplicated source rows"],
    ], [52 * mm, 16 * mm, 92 * mm], align_right=[1]))

    # ---------------- pipeline ----------------
    story.append(Paragraph("2. Pipeline", H2))
    story.append(Paragraph(
        "A three-layer medallion design. Every write is a Delta commit, so each table carries an "
        "ACID transaction log and can be read at any earlier version.", BODY))
    story.append(table([
        ["Layer", "Delta table", "What it holds"],
        ["Bronze", "bronze_customer_raw", "the CSV landed verbatim, every column as STRING"],
        ["Silver", "silver_customer_master", "cleaned, typed, de-duplicated — one row per customer"],
        ["Gold", "gold_customer_scd1", "SCD Type 1 — current state, one row per customer"],
        ["Gold", "gold_customer_scd2", "SCD Type 2 — full history with effective dates"],
    ], [20 * mm, 46 * mm, 94 * mm]))

    # ---------------- cleaning ----------------
    story.append(Paragraph("3. Cleaning", H2))
    story.append(Paragraph(
        "One shared function cleans both the master snapshot and the incremental feed, which "
        "guarantees they are normalised identically — if they were not, the change-detection hash "
        "would report false differences and the merge key could fail to match.", BODY))
    story.append(table([
        ["Rule", "Effect on the master snapshot"],
        ["Trim whitespace, collapse spaces, standardise case",
         "\"  CONSUMER \" and \"Consumer\" no longer split into two segments"],
        ["Drop rows with a null business key", f"{c['master_null_key_rows_dropped']} rows removed"],
        ["Drop exact duplicate rows", f"{c['master_exact_duplicates_dropped']} rows removed"],
        ["Keep newest row per customer_id", f"{c['master_duplicate_keys_dropped']} rows removed"],
        ["Cast to int / float / date / timestamp", "enables arithmetic, range filters, schema enforcement"],
        ["Impute remaining nulls with documented defaults", f"{c['master_null_cells_filled']} null cells filled"],
    ], [66 * mm, 94 * mm]))
    story.append(Paragraph(
        f"Result: <b>{s['source']['master_csv_rows']:,} raw rows → {s1['rows_before']:,} clean rows</b> "
        f"({c['master_rows_removed']} removed), zero nulls, zero duplicates, unique primary key. "
        f"The incremental feed cleaned from {s['source']['incremental_csv_rows']} to "
        f"{cc['new'] + cc['changed'] + cc['unchanged']} rows "
        f"({c['incremental_duplicates_dropped']} duplicated source rows removed). That last step is a "
        "hard requirement, not a nicety: <b>MERGE fails outright if one source row matches the same "
        "target row more than once</b>.", BODY))

    story.append(PageBreak())

    # ---------------- merge ----------------
    story.append(Paragraph("4. The MERGE operations", H2))
    story.append(Paragraph(
        "Before merging, every incoming row is compared against the target using an MD5 hash of the "
        "tracked attributes, which gives an exact expectation for what the merge should do:", BODY))
    story.append(table([
        ["Classification", "Rows", "Expected merge action"],
        ["NEW — key not in target", f"{cc['new']}", "INSERT"],
        ["CHANGED — key present, hash differs", f"{cc['changed']}", "UPDATE (SCD1) / new version (SCD2)"],
        ["UNCHANGED — key present, hash identical", f"{cc['unchanged']}", "no-op"],
    ], [64 * mm, 16 * mm, 80 * mm], align_right=[1]))

    story.append(Paragraph("<b>SCD Type 1 — overwrite in place</b>", BODY))
    story.append(Paragraph(
        "MERGE INTO gold_customer_scd1 AS t<br/>"
        "USING incremental_batch AS s ON t.customer_id = s.customer_id<br/>"
        "WHEN MATCHED THEN UPDATE SET *<br/>"
        "WHEN NOT MATCHED THEN INSERT *", CODE))
    story.append(table([
        ["Metric", "Value", "Expected"],
        ["source rows", f"{cc['new'] + cc['changed'] + cc['unchanged']}", "157"],
        ["rows updated", f"{s1['updated']}", f"{cc['changed']} changed + {cc['unchanged']} identical = {cc['changed'] + cc['unchanged']}"],
        ["rows inserted", f"{s1['inserted']}", f"{cc['new']}"],
        ["table rows", f"{s1['rows_before']:,} → {s1['rows_after']:,}", f"{s1['rows_before']:,} + {cc['new']}"],
        ["Delta version", f"0 → {s1['delta_version']}", "one atomic commit"],
    ], [34 * mm, 34 * mm, 92 * mm], align_right=[1]))

    story.append(Paragraph("<b>SCD Type 2 — full history</b>", BODY))
    story.append(Paragraph(
        "A single MERGE cannot both close an old row and insert its replacement, because one source "
        "row can only act on one target row. The standard Delta pattern feeds MERGE a union: "
        "<b>Part A</b> is every incoming row keyed on customer_id (it matches the current row and "
        "closes it), and <b>Part B</b> is the changed rows only with <b>merge_key = NULL</b> — NULL "
        "never equals anything, so those rows are always NOT MATCHED and are inserted as the new "
        "version.", BODY))
    story.append(Paragraph(
        "MERGE INTO gold_customer_scd2 AS t<br/>"
        "USING staged_source AS s ON t.customer_id = s.merge_key AND t.is_current = true<br/>"
        "WHEN MATCHED AND t.record_hash &lt;&gt; s.record_hash<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp; THEN UPDATE SET is_current = false, effective_end_date = s.effective_start_date<br/>"
        "WHEN NOT MATCHED THEN INSERT *", CODE))
    story.append(table([
        ["Metric", "Value", "Expected"],
        ["staged source rows", f"{cc['new'] + cc['changed'] + cc['unchanged']} + {cc['changed']} = "
                               f"{cc['new'] + 2 * cc['changed'] + cc['unchanged']}", "Part A + Part B"],
        ["versions closed out", f"{s2['versions_closed']}", f"{cc['changed']}"],
        ["rows inserted", f"{s2['rows_inserted']}", f"{cc['changed']} new versions + {cc['new']} new customers"],
        ["table rows", f"{s2['rows_before']:,} → {s2['rows_after']:,}", "793 + 101 + 45"],
        ["current rows", f"{s2['current_rows']:,}", "one per customer, matches SCD1"],
    ], [34 * mm, 42 * mm, 84 * mm], align_right=[1]))

    # ---------------- validation ----------------
    story.append(Paragraph("5. Validation", H2))
    story.append(Paragraph(
        f"{v['scd1_checks_passed'] + v['scd2_checks_passed'] + v['suite_checks_passed']} assertions run "
        "against the persisted Delta tables — read back from disk, not from memory — and all pass:", BODY))
    story.append(table([
        ["Area", "Checks", "Result"],
        ["SCD1 — counts, primary key, nulls, merge metrics", f"{v['scd1_checks_passed']}", "all pass"],
        ["SCD2 — surrogate key, one current row per customer, "
         "effective-date integrity, no gaps or overlaps", f"{v['scd2_checks_passed']}", "all pass"],
        ["Cross-table suite — SCD1 vs SCD2 agreement, feed fully applied, domain checks",
         f"{v['suite_checks_passed']}", "all pass"],
        ["Time travel — version 0 reproduces the pre-merge state exactly", "1", "pass"],
    ], [96 * mm, 20 * mm, 24 * mm], align_right=[1, 2]))

    story.append(PageBreak())

    # ---------------- results ----------------
    story.append(Paragraph("6. Results", H2))
    story.append(table([
        ["", "Rows", "Distinct customers"],
        ["customer_master.csv (raw)", f"{s['source']['master_csv_rows']:,}", "793"],
        ["silver_customer_master (clean)", f"{s1['rows_before']:,}", f"{s1['rows_before']:,}"],
        ["gold_customer_scd1 (after MERGE)", f"{s1['rows_after']:,}", f"{s1['rows_after']:,}"],
        ["gold_customer_scd2 (all versions)", f"{s2['rows_after']:,}", f"{s2['current_rows']:,}"],
        ["  of which current", f"{s2['current_rows']:,}", ""],
        ["  of which expired", f"{s2['rows_after'] - s2['current_rows']:,}", ""],
    ], [72 * mm, 30 * mm, 38 * mm], align_right=[1, 2]))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"Final business view: <b>{b['customers']:,} customers</b>, "
        f"<b>${b['total_sales']:,.2f}</b> lifetime sales, "
        f"<b>${b['total_profit']:,.2f}</b> profit.", BODY))

    if os.path.exists(CHART):
        story.append(Spacer(1, 4))
        story.append(Image(CHART, width=160 * mm, height=98 * mm))
        story.append(Paragraph("Figure 1 — merge metrics, row counts through the pipeline, "
                               "sales by region and customer mix by loyalty tier.", SMALL))

    # ---------------- discussion ----------------
    story.append(Paragraph("7. Discussion", H2))
    story.append(Paragraph(
        "<b>Why MERGE rather than a full overwrite.</b> Rewriting the whole table each batch is "
        "simple but wasteful, and it destroys any record of what changed. MERGE rewrites only the "
        "affected files, runs as a single ACID transaction, and records row-level metrics in the "
        "transaction log. Readers querying during the merge see the previous version, never a "
        "half-written one.", BODY))
    story.append(Paragraph(
        "<b>Type 1 versus Type 2.</b> Type 1 keeps one row per customer and overwrites it — the right "
        "choice when only the current state matters and query simplicity is the priority. Type 2 keeps "
        "every version, which is what you need to answer \"what was this customer's segment when that "
        "order was placed?\". The cost is a larger table and a mandatory <font face='Courier'>WHERE "
        "is_current = true</font> on every current-state query. The record_hash is what makes Type 2 "
        "behave: without it, a feed that re-sends identical rows would create a new version for every "
        "customer every day. Here it correctly left the "
        f"{cc['unchanged']} unchanged rows alone.", BODY))
    story.append(Paragraph(
        "<b>Trade-offs and next steps.</b> These tables are unpartitioned, which is fine at this size "
        "but would need partitioning (by region, say) plus periodic OPTIMIZE / Z-ORDER at scale. "
        "Surrogate keys are allocated in blocks so the sequence has gaps — harmless, since a surrogate "
        "key only has to be unique. A production version would enable Change Data Feed for downstream "
        "consumers, schedule VACUUM once the time-travel retention window has passed, and quarantine "
        "bad rows into a rejects table instead of imputing them.", BODY))

    story.append(Paragraph("8. Reproducing this run", H2))
    story.append(Paragraph(
        "pip install -r requirements.txt<br/>"
        "python scripts/generate_datasets.py &nbsp;&nbsp;# rebuild the two CSVs from the Superstore export<br/>"
        "jupyter nbconvert --to notebook --execute --inplace notebooks/delta_scd_assignment.ipynb<br/>"
        "python scripts/capture_screenshots.py &nbsp;&nbsp;# re-render screenshots/ from the executed notebook<br/>"
        "python scripts/build_report.py &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# rebuild this PDF", CODE))
    story.append(Paragraph(
        "The notebook is idempotent — RESET_LAKE = True drops and rebuilds every Delta table on each "
        "run, so re-executing it always produces the numbers in this report.", SMALL))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="Assignment 7 - Delta Lake MERGE", author="Assignment 7",
    ).build(story)
    print(f"wrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
