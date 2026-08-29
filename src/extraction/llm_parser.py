import json
import openai
from loguru import logger
from src.config import Config


class LLMParser:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.LLM_MODEL
        
    def parse_order_text(self, ocr_text: str) -> dict:
        """Use LLM to parse OCR text into structured order data"""
        logger.info("Parsing OCR text with LLM")
        
        prompt = self._build_extraction_prompt(ocr_text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from order documents. Extract all fields accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=Config.LLM_TEMPERATURE,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.success("LLM parsing completed")
            return result
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise
    
    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Build prompt for LLM extraction"""
        return f"""
        Extract the following structured data from this order document:

        {ocr_text}

        Return a JSON object with this exact structure:
        {{
            "order_date": "YYYY-MM-DD",
            "external_reference": "string",
            "debtor": {{
                "company": "string",
                "first_name": "string",
                "last_name": "string",
                "street": "string",
                "zip": "string",
                "city": "string",
                "country": "string",
                "email": "string",
                "phone": "string",
                "tax_id": "string",
                "alias": "string"
            }},
            "payment": {{
                "method": "string (Bank Transfer, Credit Card, SEPA Direct Debit, Cash, Check)",
                "status": "string (PAID or UNPAID)",
                "date": "YYYY-MM-DD (only if PAID)"
            }},
            "line_items": [
                {{
                    "sku": "string",
                    "description": "string",
                    "quantity": number,
                    "unit_net_price": number (in EUR),
                    "vat_percentage": number,
                    "discount_percentage": number
                }}
            ],
            "totals": {{
                "total_net": number,
                "total_vat": number,
                "total_gross": number
            }}
        }}

        Important rules:
        1. Dates must be in YYYY-MM-DD format
        2. All prices are in EUR
        3. VAT percentage should be a number (e.g., 19, 0, 7.7)
        4. If a field is not found, use null
        5. For payment status, look for keywords like "paid", "bezahlt", "payment received"
        6. For payment method, look for bank transfer, credit card, SEPA, etc.
        7. Clean up OCR artifacts (misread characters, extra spaces)
        8. Ensure all numbers are properly formatted
        """