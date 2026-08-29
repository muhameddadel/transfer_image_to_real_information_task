import time
from loguru import logger
from src.automation.uia_controller import UIAController
from src.config import Config


class ProductFlow:
    def __init__(self, uia_controller: UIAController):
        self.uia = uia_controller
        self.product_window = None
        
    def resolve_or_create_product(self, item_data: dict):
        """Resolve existing Product or create new one"""
        logger.info(f"Resolving Product: {item_data.get('sku')}")
        
        if self._search_existing_product(item_data):
            logger.success(f"Found existing Product: {item_data.get('sku')}")
            return
        
        self._ensure_vat_exists(item_data.get('vat_percentage', 19))
        
        logger.info(f"Creating new Product: {item_data.get('sku')}")
        self._create_new_product(item_data)
        
        self._select_new_product_in_order(item_data)
    
    def _search_existing_product(self, item_data: dict) -> bool:
        """Search for existing Product in Fakturama"""
        logger.info(f"Searching for Product: {item_data.get('sku')}")
        
        try:
            search_icon = self.uia.window.ButtonControl(Name="Select product")
            search_icon.Click()
        except:
            items_table = self.uia.window.PaneControl(Name="Items")
            if items_table.Exists(1):
                icons = items_table.GetChildren()
                for icon in icons:
                    if "product" in str(icon.GetName()).lower():
                        icon.Click()
                        break
        
        time.sleep(0.5)
        
        select_dialog = self.uia.window.WindowControl(Name="Select a product")
        if not select_dialog.Exists(Config.ELEMENT_TIMEOUT):
            logger.warning("Could not open product selector")
            return False
        
        search_field = select_dialog.EditControl(AutomationId="searchField")
        if search_field.Exists(1):
            search_field.SetValue(item_data.get('sku', ''))
            time.sleep(0.5)
        else:
            select_dialog.FindControl(Name="Search").SetValue(item_data.get('sku', ''))
            time.sleep(0.5)
        
        results_list = select_dialog.ListControl()
        if results_list.Exists(1):
            items = results_list.GetChildren()
            if len(items) == 1:
                item = items[0]
                if item_data.get('sku', '').lower() in item.GetName().lower():
                    item.Click()
                    self.uia.click_element(Name="OK", ControlType="Button", window=select_dialog)
                    return True
            elif len(items) > 1:
                for item in items:
                    if item_data.get('sku', '').lower() in item.GetName().lower():
                        item.Click()
                        self.uia.click_element(Name="OK", ControlType="Button", window=select_dialog)
                        return True
        
        self.uia.click_element(Name="Cancel", ControlType="Button", window=select_dialog)
        return False
    
    def _ensure_vat_exists(self, vat_percentage: float):
        """Ensure VAT rate exists in Fakturama"""
        logger.info(f"Ensuring VAT {vat_percentage}% exists")
        
        self.uia.click_element(Name="Data", ControlType="MenuItem")
        time.sleep(0.2)
        self.uia.click_element(Name="VATs", ControlType="MenuItem")
        time.sleep(0.5)
        
        vat_dialog = self.uia.window.WindowControl(Name="VATs")
        if not vat_dialog.Exists(Config.ELEMENT_TIMEOUT):
            logger.warning("Could not open VATs dialog")
            return
        
        vat_name = f"VAT {vat_percentage}%"
        vat_items = vat_dialog.ListControl().GetChildren()
        
        found = False
        for item in vat_items:
            if vat_name.lower() in item.GetName().lower():
                found = True
                break
        
        if not found:
            logger.info(f"Creating new VAT: {vat_name}")
            self.uia.click_element(Name="New", ControlType="Button", window=vat_dialog)
            time.sleep(0.3)
            
            name_field = vat_dialog.EditControl(Name="Name")
            name_field.SetValue(vat_name)
            
            desc_field = vat_dialog.EditControl(Name="Description")
            desc_field.SetValue(vat_name)
            
            code_combo = vat_dialog.ComboBoxControl(Name="VAT code (E-Invoice)")
            code_combo.SetValue("S")
            
            value_field = vat_dialog.EditControl(Name="Value")
            value_field.SetValue(str(vat_percentage))
            
            self.uia.click_element(Name="Save", ControlType="Button", window=vat_dialog)
            time.sleep(0.5)
            
            logger.success(f"Created VAT: {vat_name}")
        
        self.uia.click_element(Name="Close", ControlType="Button", window=vat_dialog)
        time.sleep(0.3)
    
    def _create_new_product(self, item_data: dict):
        """Create new Product in Fakturama"""
        logger.info(f"Creating new Product: {item_data.get('sku')}")
        
        self.uia.click_element(Name="New product", ControlType="Button")
        time.sleep(0.5)
        
        self.product_window = self.uia.window.WindowControl(Name="New Product")
        if not self.product_window.Exists(Config.ELEMENT_TIMEOUT):
            self.product_window = self.uia.window.WindowControl(Name="Product")
        
        if not self.product_window.Exists(Config.ELEMENT_TIMEOUT):
            raise Exception("Could not open Product editor")
        
        sku_field = self.product_window.EditControl(Name="Item Number")
        sku_field.SetValue(item_data.get('sku', ''))
        
        name_field = self.product_window.EditControl(Name="Name")
        name_field.SetValue(item_data.get('description', ''))
        
        desc_field = self.product_window.EditControl(Name="Description")
        desc_field.SetValue(item_data.get('description', ''))
        
        unit_net = item_data.get('unit_net_price', 0)
        vat_pct = item_data.get('vat_percentage', 19)
        price_gross = round(unit_net * (1 + vat_pct / 100), 2)
        
        price_field = self.product_window.EditControl(Name="Price (gross)")
        price_field.SetValue(str(price_gross))
        
        cost_field = self.product_window.EditControl(Name="cost price (net)")
        cost_field.SetValue("0.00")
        
        vat_combo = self.product_window.ComboBoxControl(Name="VAT")
        vat_name = f"VAT {vat_pct}%"
        vat_combo.SetValue(vat_name)
        
        stock_field = self.product_window.EditControl(Name="Stock")
        stock_field.SetValue("0.00")
        
        self.uia.click_element(Name="Save", ControlType="Button", window=self.product_window)
        time.sleep(1)
        
        self.uia.click_element(Name="Close", ControlType="Button", window=self.product_window)
        time.sleep(0.5)
        
        logger.success(f"Created Product: {item_data.get('sku')}")
    
    def _select_new_product_in_order(self, item_data: dict):
        """Return to Order and select the newly created Product"""
        logger.info(f"Selecting new Product in Order: {item_data.get('sku')}")
        
        self.uia.window.WindowControl(Name="Order").SetFocus()
        time.sleep(0.5)
        
        self._search_existing_product(item_data)
        
        logger.success(f"New Product selected in Order: {item_data.get('sku')}")
    
    def complete_line_item(self, item_data: dict):
        """Complete line item in Order"""
        logger.info(f"Completing line item: {item_data.get('sku')}")
        
        qty_field = self.uia.window.EditControl(Name="Qty.")
        qty_field.SetValue(str(item_data.get('quantity', 1)))
        
        price_field = self.uia.window.EditControl(Name="U.Price")
        price_field.SetValue(str(item_data.get('unit_net_price', 0)))
        
        vat_combo = self.uia.window.ComboBoxControl(Name="VAT")
        vat_name = f"VAT {item_data.get('vat_percentage', 19)}%"
        vat_combo.SetValue(vat_name)
        
        discount = item_data.get('discount_percentage', 0)
        if discount != 0:
            discount_field = self.uia.window.EditControl(Name="Discount")
            discount_field.SetValue(str(discount))
        
        expected_price = item_data.get('quantity', 1) * item_data.get('unit_net_price', 0) * (1 - discount / 100)
        price_display = self.uia.window.TextControl(Name="Price").GetValue()
        try:
            actual_price = float(price_display.replace('€', '').replace(',', '.').strip())
            if abs(expected_price - actual_price) > 0.01:
                logger.warning(f"Line price mismatch: expected {expected_price}, actual {actual_price}")
        except:
            pass