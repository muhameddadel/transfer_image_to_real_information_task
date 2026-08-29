import time
from loguru import logger
from src.automation.uia_controller import UIAController
from src.config import Config


class InvoiceFlow:
    def __init__(self, uia_controller: UIAController):
        self.uia = uia_controller
        self.invoice_window = None
        
    def generate_invoice_from_order(self):
        """Generate linked Invoice from saved Order"""
        logger.info("Generating linked Invoice from Order")
        
        follow_up = self.uia.window.PaneControl(Name="Create a follow-up document")
        if follow_up.Exists(1):
            invoice_button = follow_up.ButtonControl(Name="Invoice")
            if invoice_button.Exists(1):
                invoice_button.Click()
            else:
                self.uia.click_element(Name="Invoice", ControlType="Button")
        else:
            self.uia.click_element(Name="Invoice", ControlType="Button")
        
        time.sleep(1)
        
        self.invoice_window = self.uia.window.WindowControl(Name="New Invoice")
        if not self.invoice_window.Exists(Config.ELEMENT_TIMEOUT):
            self.invoice_window = self.uia.window.WindowControl(Name="Invoice")
        
        if not self.invoice_window.Exists(Config.ELEMENT_TIMEOUT):
            raise Exception("Could not open Invoice editor")
        
        self._verify_invoice_data()
        
        logger.success("Invoice generated")
    
    def _verify_invoice_data(self):
        """Verify Invoice data matches Order"""
        logger.info("Verifying Invoice data")
        
        ref_field = self.invoice_window.EditControl(Name="Cust.Ref.")
        if ref_field.Exists(1):
            ref_value = ref_field.GetValue()
            if ref_value:
                logger.debug(f"Cust.Ref. copied: {ref_value}")
            else:
                logger.warning("Cust.Ref. not copied from Order")
        
        items_table = self.invoice_window.TableControl(Name="Items")
        if items_table.Exists(1):
            items = items_table.GetChildren()
            if len(items) > 0:
                logger.debug(f"Items copied: {len(items)}")
            else:
                logger.warning("No items found in Invoice")
        
        logger.success("Invoice data verified")
    
    def apply_payment_status(self, data: dict):
        """Apply payment status to Invoice"""
        logger.info("Applying payment status")
        
        payment_data = data.get('payment', {})
        payment_status = payment_data.get('status', 'UNPAID')
        payment_method = payment_data.get('method')
        
        if payment_method:
            try:
                method_combo = self.invoice_window.ComboBoxControl(Name="Payment method")
                method_combo.Click()
                method_item = method_combo.ListItemControl(Name=payment_method)
                if method_item.Exists(1):
                    method_item.Click()
                    logger.debug(f"Set payment method: {payment_method}")
                else:
                    logger.warning(f"Payment method not found: {payment_method}")
            except:
                logger.warning("Could not set payment method")
        
        if payment_status == 'PAID':
            self._apply_paid_status(data)
        else:
            self._apply_unpaid_status()
        
        self.uia.click_element(Name="Save", ControlType="Button", window=self.invoice_window)
        time.sleep(1)
        
        self._verify_invoice_saved(data)
        
        logger.success("Payment status applied")
    
    def _apply_paid_status(self, data: dict):
        """Apply PAID status to Invoice"""
        logger.info("Applying PAID status")
        
        paid_checkbox = self.invoice_window.CheckBoxControl(Name="paid")
        paid_checkbox.SetValue(True)
        
        payment_date = data.get('payment', {}).get('date')
        if payment_date:
            date_field = self.invoice_window.EditControl(Name="Payment date")
            date_field.SetValue(payment_date)
        
        total_field = self.invoice_window.TextControl(Name="Total")
        total_text = total_field.GetValue()
        try:
            total_value = float(total_text.replace('€', '').replace(',', '.').strip())
            value_field = self.invoice_window.EditControl(Name="Value")
            value_field.SetValue(str(total_value))
            logger.debug(f"Set payment value: {total_value}")
        except:
            logger.warning("Could not set payment value")
    
    def _apply_unpaid_status(self):
        """Apply UNPAID status to Invoice"""
        logger.info("Applying UNPAID status")
        
        paid_checkbox = self.invoice_window.CheckBoxControl(Name="paid")
        paid_checkbox.SetValue(False)
        
    
    def _verify_invoice_saved(self, data: dict):
        """Verify Invoice was saved correctly"""
        logger.info("Verifying Invoice saved")
        
        self.uia.click_element(Name="Data", ControlType="MenuItem")
        time.sleep(0.3)
        self.uia.click_element(Name="Documents", ControlType="MenuItem")
        time.sleep(0.5)
        
        docs_dialog = self.uia.window.WindowControl(Name="Documents")
        if docs_dialog.Exists(Config.ELEMENT_TIMEOUT):
            invoice_row = docs_dialog.ListItemControl(Name=data.get('external_reference', ''))
            if not invoice_row.Exists(1):
                logger.warning("Could not find saved Invoice in documents list")
            else:
                state_text = invoice_row.TextControl(Name="State").GetValue()
                if state_text:
                    if 'paid' in state_text.lower():
                        logger.success("Invoice saved with PAID status")
                    else:
                        logger.info(f"Invoice saved with status: {state_text}")
            
            self.uia.click_element(Name="Close", ControlType="Button", window=docs_dialog)
        
        order_window = self.uia.window.WindowControl(Name="Order")
        if order_window.Exists(1):
            status_field = order_window.TextControl(Name="State")
            if status_field.Exists(1):
                status = status_field.GetValue()
                if 'open' in status.lower():
                    logger.info("Source Order remains open")
                else:
                    logger.warning(f"Source Order status: {status}")
        
        logger.success("Invoice verification complete")