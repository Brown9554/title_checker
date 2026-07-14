# Title Chain Analyzer

Title Chain Analyzer is an AI-assisted tool for homeowners, buyers, and real estate professionals who need to identify potential title defects in Massachusetts residential properties before closing. By analyzing recorded registry of deeds documents, it helps surface issues such as unreleased mortgages, chain-of-title gaps, and other encumbrances that can cause costly delays or litigation. The project was inspired by a real title snag experience in which a seemingly routine transaction was delayed by a document that was publicly recorded but buried in a stack of scanned PDFs and easy to miss without expert review.

## The Problem

Title defects are often invisible at first glance, but they can have outsized consequences at closing. An unreleased mortgage, a missing discharge, or an incomplete chain of title can delay a sale, create refinancing risk, or force a last-minute legal scramble. The information needed to detect these issues is publicly available through Massachusetts land records, but it is typically scattered across dozens of scanned registry documents and written in a format that requires specialized interpretation. This tool exists to make that process faster, more structured, and more accessible.

## How It Works

The analysis pipeline is designed to mirror the way a title professional would investigate a property history:

1. PDF documents are loaded from the Massachusetts Registry of Deeds records.
2. Claude Vision is used to OCR and interpret each page image.
3. Extracted text is passed through entity extraction logic that identifies deeds, mortgages, liens, parties, dates, and references.
4. The resulting entities are analyzed to reconstruct the chain of title and identify potential defects.
5. A risk report is generated highlighting issues that may require deeper review.

## Document Types Supported

The system currently supports the following document types from the taxonomy:

- Deed
  - Warranty deed
  - Quitclaim deed
  - Grant deed
  - Executor deed
- Mortgage
- Discharge
- Municipal lien
- Homestead
- Notice
- Assignment
- Subordination
- Affidavit
- Power of attorney
- Probate
- Release
- Reconveyance

## Risk Flags Detected

The analyzer is designed to identify the following risk flags:

- Unreleased mortgage
- Gap in chain
- Missing discharge
- Unresolved notice
- Assignment without discharge
- Duplicate homestead
- Municipal lien at closing
- Incomplete document set

## Tech Stack

- Python
- Anthropic Claude API (Vision + Text)
- pdfplumber for PDF parsing and page rendering
- Massachusetts Registry of Deeds documents as the source domain

## Project Status

Early development / work in progress.

## Setup

1. Clone the repository.
2. Create and activate a Python environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## Usage

Usage details will be added as the project evolves.
