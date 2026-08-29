import re
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger


class DataNormalizer:
    def parse_ocr_text(self, ocr_text: str) -> dict:
        """Parse OCR text using regex patterns (fallback when LLM unavailable)"""
        logger.info("Parsing OCR text with regex patterns")
        
        result = {
            "order_date": None,
            "external_reference": None,
            "debtor": {},
            "payment": {},
            "line_items": [],
            "totals": {}
        }
        
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}\.\d{2}\.\d{4})',
            r'(\d{2}/\d{2}/\d{4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, ocr_text)
            if match:
                date_str = match.group(1)
                try:
                    if '.' in date_str or '/' in date_str:
                        parts = re.split(r'[/.]', date_str)
                        result['order_date'] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                    else:
                        result['order_date'] = date_str
                    break
                except:
                    continue
        
        company_patterns = [
            r'(?:Company|Firma|Customer|Kunde):?\s*([A-Z][A-Za-z0-9\s&\.\-]+)',
            r'^([A-Z][A-Za-z0-9\s&\.\-]+)$'  # Line starting with company name
        ]
        for pattern in company_patterns:
            match = re.search(pattern, ocr_text, re.MULTILINE)
            if match:
                result['debtor']['company'] = match.group(1).strip()
                break
        
        paid_patterns = [
            r'status:\s*(paid|bezahlt|payment received)',
            r'(paid|bezahlt)',
        ]
        for pattern in paid_patterns:
            if re.search(pattern, ocr_text, re.IGNORECASE):
                result['payment']['status'] = 'PAID'
                break
        if 'status' not in result['payment']:
            result['payment']['status'] = 'UNPAID'
        
        method_patterns = {
            'Bank Transfer': r'(bank transfer|überweisung|banküberweisung)',
            'Credit Card': r'(credit card|kreditkarte|visa|mastercard)',
            'SEPA Direct Debit': r'(sepa|direct debit|lastschrift)',
            'Cash': r'(cash|bar)',
            'Check': r'(check|scheck)'
        }
        for method, pattern in method_patterns.items():
            if re.search(pattern, ocr_text, re.IGNORECASE):
                result['payment']['method'] = method
                break
        
        item_pattern = r'(?:SKU|Art|Item|Artikel)?\s*([A-Z0-9\-]+)\s+([A-Za-z0-9\s\-]+?)\s+(\d+\.?\d*)\s+([\d\.,]+)\s+([\d\.,]+)%?\s+([\d\.,]+)'
        matches = re.findall(item_pattern, ocr_text, re.IGNORECASE)
        for match in matches:
            try:
                result['line_items'].append({
                    'sku': match[0].strip(),
                    'description': match[1].strip(),
                    'quantity': float(match[2].replace(',', '.')),
                    'unit_net_price': float(match[3].replace(',', '.')),
                    'vat_percentage': float(match[4].replace(',', '.')),
                    'discount_percentage': float(match[5].replace(',', '.')) if len(match) > 5 else 0
                })
            except:
                continue
        
        total_patterns = {
            'total_net': r'(?:Net|Netto|Total Net):?\s*([\d\.,]+)',
            'total_vat': r'(?:VAT|Tax|USt):?\s*([\d\.,]+)',
            'total_gross': r'(?:Gross|Total|Brutto):?\s*([\d\.,]+)'
        }
        for key, pattern in total_patterns.items():
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                val = match.group(1).replace(',', '.')
                try:
                    result['totals'][key] = float(val)
                except:
                    continue
        
        logger.success("Regex parsing completed")
        return result