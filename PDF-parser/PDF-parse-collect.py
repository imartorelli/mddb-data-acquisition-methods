"""
PDF-parse-collect.py — PDF parser for detecting sequence archive accession numbers.

Reads a folder of article PDFs and a DOI list CSV, extracts INSDC accession
numbers from each PDF, and produces a combined accession report.

Usage (interactive):
    python3 PDF-parse-collect.py

Usage (command line):
    python3 PDF-parse-collect.py.py --folder <article-folder> --doi <doi_list.csv>

    --folder   Path to the folder containing the article PDFs
               (may be named 'article-list', 'FetchSRAfromPDF', or anything else)
    --doi      Path to the DOI list CSV (columns: article, doi)
               If not provided, the script looks for doi_list.csv inside the folder
               or its results/ subfolder.
    --out      Path for the output CSV report (default: <folder>/results/doi_accession_report.csv)

Dependencies:
    pip install pypdf

the other dependencies are available
"""

import csv
import os
import re
import sys

try:
    import pypdf
except ImportError:
    print("Missing dependency — install with: pip install pypdf")
    sys.exit(1)


# ── Accession patterns ─────────────────────────────────────────────────────────
# I searched for the general DOMAIN names for accession numbers obtained from the general sequence data repositories. This was done manually

ACCESSION_PATTERNS = [
    ("SRP",   re.compile(r"SRP\d{6,9}"),   r"SRP\d{6,9}"),
    ("SRS",   re.compile(r"SRS\d{6,9}"),   r"SRS\d{6,9}"),
    ("SRX",   re.compile(r"SRX\d{6,9}"),   r"SRX\d{6,9}"),
    ("SRR",   re.compile(r"SRR\d{6,9}"),   r"SRR\d{6,9}"),
    ("PRJNA", re.compile(r"PRJNA\d{5,9}"), r"PRJNA\d{5,9}"),
    ("ERP",   re.compile(r"ERP\d{6,9}"),   r"ERP\d{6,9}"),
    ("PRJEB", re.compile(r"PRJEB\d{5,9}"), r"PRJEB\d{5,9}"),
]


# Make sure you controll the list provided

def extract_text(pdf_path):
    """Return concatenated text from all pages, or None on error."""
    try:
        reader = pypdf.PdfReader(open(pdf_path, "rb"))
    except Exception as e:
        print(f"  [error] Could not open {pdf_path}: {e}")
        return None
    parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(parts)


def find_accessions(text):
    """Return list of (prefix, accession, regex_str) for all unique matches."""
    hits, seen = [], set()
    for prefix, pattern, pattern_str in ACCESSION_PATTERNS:
        for m in pattern.finditer(text):
            acc = m.group(0)
            if acc not in seen:
                hits.append((prefix, acc, pattern_str))
                seen.add(acc)
    return hits


# module for checking if the doi list maps to the article list provided

def load_doi_list(doi_path):
    """
    Load DOI list CSV (columns: article, doi).
    Returns dict {article_label: doi}.
    """
    mapping = {}
    with open(doi_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            art = row.get("article", "").strip().replace(".pdf", "")
            doi = row.get("doi", "").strip()
            if art:
                mapping[art] = doi
    return mapping


def find_doi_file(folder):
    """Look for doi_list.csv in the folder or its results/ subfolder."""
    candidates = [
        os.path.join(folder, "doi_list.csv"),
        os.path.join(folder, "results", "doi_list.csv"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

# make sure you check if the articles are downloaded in pdf format. This prevents that the pdf is not directly accessible (i.e. need institutional credentials)
def collect_pdfs(folder):
    """Return sorted list of PDF paths in a folder."""
    return sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    ])


# Make sure you return your results here, printed version for reports

def print_report(rows):
    print()
    print(f"{'Article':<10}  {'DOI':<40}  {'Prefix':<7}  {'Accession':<18}  Regex")
    print("-" * 100)
    for r in rows:
        print(f"{r['article']:<10}  {r['doi']:<40}  {r['prefix']:<7}  "
              f"{r['accession']:<18}  {r['regex']}")
    print()


def save_report(rows, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["article", "doi", "prefix", "accession", "regex_pattern", "status"])
        writer.writerows([
            [r["article"], r["doi"], r["prefix"], r["accession"], r["regex"], r["status"]]
            for r in rows
        ])
    print(f"Report saved to: {out_path}")


# Request the list from user

def prompt_doi_file_interactive():
    """Ask the user for the doi_list.csv file path."""
    print("\nthis is the PDF-parse-collect.py: PDF Accession Parser for digging the datasource in the manuscript")
    print("This script reads a doi_list.csv file and a folder of article PDFs,")
    print("extracts sequence archive accession numbers, and returns the results in a csv format, file named pdf_accession_report.csv that will be saved in the same folder where you run this script.")
    print()
    path = input("provide me the doi_list.csv file: ").strip()
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        sys.exit(1)
    return path


def prompt_folder():
    """Ask the user for the folder containing article PDFs."""
    path = input("I need to check that the DOI list maps to the article PDF folder. Please provide me the path to the folder containing article PDFs: ").strip().rstrip("/")
    if not os.path.isdir(path):
        print(f"Folder not found: {path}")
        sys.exit(1)
    return path


# ── Main ───────────────────────────────────────────────────────────────────────

def main(folder, doi_path, out_path):
    print(f"\nLoading DOI list from: {doi_path}")
    doi_map = load_doi_list(doi_path)
    print(f"  {len(doi_map)} articles loaded.")

    pdfs = collect_pdfs(folder)
    print(f"\nProcessing {len(pdfs)} PDF(s) in: {folder}")

    all_rows = []
    for pdf_path in pdfs:
        filename  = os.path.basename(pdf_path)
        art_label = filename.replace(".pdf", "")
        doi       = doi_map.get(art_label, "")
        print(f"  {filename}")

        text = extract_text(pdf_path)
        if text is None:
            all_rows.append({
                "article": art_label, "doi": doi, "prefix": "ERROR",
                "accession": "could not read PDF", "regex": "", "status": "error"
            })
            continue

        accessions = find_accessions(text)
        if not accessions:
            all_rows.append({
                "article": art_label, "doi": doi, "prefix": "",
                "accession": "NOT DETECTED", "regex": "", "status": "not detected"
            })
        else:
            for prefix, acc, regex in accessions:
                all_rows.append({
                    "article": art_label, "doi": doi, "prefix": prefix,
                    "accession": acc, "regex": regex, "status": "detected"
                })

    print_report(all_rows)
    save_report(all_rows, out_path)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse optional CLI flags
    def get_arg(flag):
        if flag in args:
            idx = args.index(flag)
            return args[idx + 1] if idx + 1 < len(args) else None
        return None

    folder   = get_arg("--folder")
    doi_path = get_arg("--doi")
    out_path = get_arg("--out")

    # Fall back to interactive prompts for missing values
    if not doi_path:
        doi_path = prompt_doi_file_interactive()

    if not folder:
        folder = prompt_folder()
    elif not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        sys.exit(1)

    if not out_path:
        out_path = os.path.join(folder, "results", "doi_accession_report.csv")

    main(folder, doi_path, out_path)
