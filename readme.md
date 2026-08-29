# Fakturama Image-to-Cash Automation

Automate the transformation of order images into fully processed Orders and Invoices in Fakturama.

## Features

- **OCR + LLM Extraction**: Intelligent data extraction from order images
- **Microsoft UI Automation**: Reliable, coordinate-free UI interaction
- **Step-by-Step Verification**: Verify each action before proceeding
- **Automatic Master Data Resolution**: Find or create Debtors and Products
- **Payment Status Handling**: Correctly apply PAID/UNPAID status

## Installation

### Prerequisites

- Python 3.9 or higher
- Fakturama desktop application
- Tesseract OCR
- OpenAI API key (optional, for LLM extraction)

### Install Dependencies

```bash
pip install -r requirements.txt