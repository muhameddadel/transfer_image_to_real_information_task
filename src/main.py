import sys
import time
import click
from pathlib import Path
from loguru import logger

from src.config import Config
from src.extraction.ocr_engine import OCREngine
from src.extraction.llm_parser import LLMParser
from src.extraction.data_normalizer import DataNormalizer
from src.automation.uia_controller import UIAController
from src.automation.order_flow import OrderFlow
from src.automation.debtor_flow import DebtorFlow
from src.automation.product_flow import ProductFlow
from src.automation.invoice_flow import InvoiceFlow
from src.verification.validators import Validator
from src.utils.logger import setup_logger


@click.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Extract but do not automate UI')
@click.option('--llm-enabled', is_flag=True, help='Enable LLM for extraction')
def main(image_path: str, dry_run: bool, llm_enabled: bool):
    """
    Fakturama Image-to-Cash Automation
    """
    
    setup_logger()
    logger.info(f"Starting Fakturama automation for image: {image_path}")
    logger.info(f"Dry run: {dry_run}, LLM enabled: {llm_enabled}")
    
    try:
        logger.info("Step 1: Extracting data from image")
        extracted_data = extract_data(image_path, llm_enabled)
        logger.success(f"Extracted data: {extracted_data}")
        
        if dry_run:
            logger.info("Dry run complete - no UI automation performed")
            return
        
        logger.info("Step 2: Connecting to Fakturama")
        uia = UIAController()
        uia.connect_to_fakturama()
        logger.success("Connected to Fakturama")
        
        logger.info("Step 3: Creating new Order")
        order_flow = OrderFlow(uia)
        order_flow.open_new_order(extracted_data)
        logger.success("Order created with basic fields")
        
        logger.info("Step 4: Resolving Debtor")
        debtor_flow = DebtorFlow(uia)
        debtor_flow.resolve_or_create_debtor(extracted_data)
        logger.success("Debtor resolved")
        
        logger.info("Step 5: Resolving Products")
        product_flow = ProductFlow(uia)
        for item in extracted_data.line_items:
            product_flow.resolve_or_create_product(item)
            product_flow.complete_line_item(item)
            logger.success(f"Product completed: {item.sku}")
        
        logger.info("Step 6: Completing Order")
        order_flow.complete_order(extracted_data)
        logger.success("Order saved")
        
        logger.info("Step 7: Generating linked Invoice")
        invoice_flow = InvoiceFlow(uia)
        invoice_flow.generate_invoice_from_order()
        logger.success("Invoice generated")
        
        logger.info("Step 8: Applying payment status")
        invoice_flow.apply_payment_status(extracted_data)
        logger.success("Payment status applied")
        
        logger.info("Step 9: Final verification")
        Validator.verify_all(order_flow, invoice_flow, extracted_data)
        logger.success("✅ All verifications passed!")
        
        logger.info("Process completed successfully!")
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        try:
            uia = UIAController()
            uia.capture_screenshot("error_state")
        except:
            pass
        sys.exit(1)


def extract_data(image_path: str, use_llm: bool) -> dict:
    """Extract structured data from image using OCR and optionally LLM"""
    ocr_engine = OCREngine()
    ocr_text = ocr_engine.extract_text(image_path)
    logger.debug(f"OCR extracted {len(ocr_text)} characters")
    
    if use_llm and Config.OPENAI_API_KEY:
        llm_parser = LLMParser()
        structured_data = llm_parser.parse_order_text(ocr_text)
    else:
        normalizer = DataNormalizer()
        structured_data = normalizer.parse_ocr_text(ocr_text)
    
    validator = Validator()
    validator.validate_extracted_data(structured_data)
    
    return structured_data


if __name__ == "__main__":
    main()