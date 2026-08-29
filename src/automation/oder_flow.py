import time
from loguru import logger
from src.automation.uia_controller import UIAController
from src.config import Config


class OrderFlow:
    def __init__(self, uia_controller: UIAController):
        self.uia = uia_controller
        self.order_window = None
        
    def open_new_order(self, data: dict):
        """Open a new Order and set basic fields"""
        logger.info("Opening new Order")
        
        self.uia.click_element(Name="Order", ControlType="Button")
        time.sleep(1)
        
        self.order_window = self.uia.window.WindowControl(Name="New Order")
        if not self.order_window.Exists(Config.ELEMENT_TIMEOUT):
            self.order_window = self.uia.window.WindowControl(Name="Order")
        
        if not self.order_window.Exists(Config.ELEMENT_TIMEOUT):
            raise Exception("Could not find Order editor window")
        
        self._set_order_fields(data)
        
        time.sleep(0.5)
    
    def _set_order_fields(self, data: dict):
        """Set Order fields: Date, Cust.Ref., Price Mode, VAT"""
        logger.info("Setting Order fields")
        
        if data.get('order_date'):
            date_field = self.order_window.EditControl(Name="Date")
            date_field.WaitForEnabled(Config.ELEMENT_TIMEOUT)
            date_field.SetValue(data['order_date'])
            logger.debug(f"Set Date: {data['order_date']}")
        
        if data.get('external_reference'):
            ref_field = self.order_window.EditControl(Name="Cust.Ref.")
            ref_field.WaitForEnabled(Config.ELEMENT_TIMEOUT)
            ref_field.SetValue(data['external_reference'])
            logger.debug(f"Set Cust.Ref.: {data['external_reference']}")
        
        try:
            price_mode = self.order_window.ComboBoxControl(Name="Price mode")
            price_mode.WaitForEnabled(Config.ELEMENT_TIMEOUT)
            price_mode.Click()
            net_item = price_mode.ListItemControl(Name="Net")
            if net_item.Exists(Config.ELEMENT_TIMEOUT):
                net_item.Click()
                logger.debug("Set Price Mode: Net")
        except:
            price_mode = self.order_window.ComboBoxControl(AutomationId="comboPriceMode")
            price_mode.SetValue("Net")
        
        try:
            vat_mode = self.order_window.ComboBoxControl(Name="VAT")
            vat_mode.WaitForEnabled(Config.ELEMENT_TIMEOUT)
            vat_mode.Click()
            with_vat = vat_mode.ListItemControl(Name="With VAT")
            if with_vat.Exists(Config.ELEMENT_TIMEOUT):
                with_vat.Click()
                logger.debug("Set VAT: With VAT")
        except:
            pass
    
    def complete_order(self, data: dict):
        """Complete and save the Order"""
        logger.info("Completing Order")
        
        if 'overall_discount' in data and data['overall_discount'] != 0:
            discount_field = self.order_window.EditControl(Name="Discount")
            discount_field.SetValue(str(data['overall_discount']))
        
        if 'shipping' in data and data['shipping']:
            shipping_field = self.order_window.EditControl(Name="Shipping")
            shipping_field.SetValue(str(data['shipping']))
        
        self._verify_order_totals(data)
        
        self.uia.click_element(Name="Save", ControlType="Button")
        time.sleep(1)
        
        self._verify_order_saved(data)
    
    def _verify_order_totals(self, data: dict):
        """Verify order totals match extracted data"""
        logger.info("Verifying order totals")
        
        total_net_text = self.order_window.TextControl(Name="Total Net").GetValue()
        total_vat_text = self.order_window.TextControl(Name="VAT").GetValue()
        total_gross_text = self.order_window.TextControl(Name="Total").GetValue()
        
        tolerance = Config.TOTAL_TOLERANCE
        
        if data.get('totals', {}).get('total_net'):
            expected = data['totals']['total_net']
            actual = float(total_net_text.replace('€', '').replace(',', '.').strip())
            if abs(expected - actual) > tolerance:
                logger.warning(f"Net total mismatch: expected {expected}, actual {actual}")
        
        if data.get('totals', {}).get('total_gross'):
            expected = data['totals']['total_gross']
            actual = float(total_gross_text.replace('€', '').replace(',', '.').strip())
            if abs(expected - actual) > tolerance:
                logger.warning(f"Gross total mismatch: expected {expected}, actual {actual}")
    
    def _verify_order_saved(self, data: dict):
        """Verify Order was saved correctly"""
        logger.info("Verifying Order saved")
        
        self.uia.click_element(Name="Data", ControlType="MenuItem")
        time.sleep(0.3)
        self.uia.click_element(Name="Documents", ControlType="MenuItem")
        time.sleep(0.5)
        
        docs_dialog = self.uia.window.WindowControl(Name="Documents")
        if docs_dialog.Exists(Config.ELEMENT_TIMEOUT):
            order_row = docs_dialog.ListItemControl(Name=data.get('external_reference', ''))
            if not order_row.Exists(1):
                logger.warning("Could not find saved Order in documents list")
            else:
                logger.success("Order found in documents")
            
            self.uia.click_element(Name="Close", ControlType="Button")
        
        self.order_window.SetFocus()