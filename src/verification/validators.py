from loguru import logger
from src.config import Config


class Validator:
    @staticmethod
    def validate_extracted_data(data: dict) -> bool:
        """Validate extracted data structure and content"""
        logger.info("Validating extracted data")
        
        errors = []
        
        if not data.get('order_date'):
            errors.append("Missing order_date")
        
        if not data.get('debtor', {}).get('company'):
            errors.append("Missing debtor company")
        
        if not data.get('line_items'):
            errors.append("No line items found")
        else:
            for i, item in enumerate(data['line_items']):
                if not item.get('sku'):
                    errors.append(f"Line item {i+1}: missing SKU")
                if not item.get('quantity'):
                    errors.append(f"Line item {i+1}: missing quantity")
                if not item.get('unit_net_price'):
                    errors.append(f"Line item {i+1}: missing unit price")
        
        totals = data.get('totals', {})
        if totals.get('total_gross'):
            net = totals.get('total_net', 0)
            vat = totals.get('total_vat', 0)
            gross = totals.get('total_gross', 0)
            if abs(gross - (net + vat)) > 0.01:
                errors.append(f"Total mismatch: {net} + {vat} != {gross}")
        
        if errors:
            for error in errors:
                logger.error(f"Validation error: {error}")
            raise ValueError(f"Data validation failed: {', '.join(errors)}")
        
        logger.success("Data validation passed")
        return True
    
    @staticmethod
    def verify_all(order_flow, invoice_flow, data: dict) -> bool:
        """Verify entire flow completion"""
        logger.info("Performing final verification")
        
        order_flow._verify_order_saved(data)
        
        invoice_flow._verify_invoice_saved(data)
        
        logger.success("All verifications passed")
        return True