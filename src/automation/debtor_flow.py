import time
from loguru import logger
from src.automation.uia_controller import UIAController
from src.config import Config


class DebtorFlow:
    def __init__(self, uia_controller: UIAController):
        self.uia = uia_controller
        self.debtor_window = None
        
    def resolve_or_create_debtor(self, data: dict):
        """Resolve existing Debtor or create new one"""
        logger.info("Resolving Debtor")
        
        debtor_data = data.get('debtor', {})
        
        if self._search_existing_debtor(debtor_data):
            logger.success("Found existing Debtor")
            return
        
        logger.info("Creating new Debtor")
        self._create_new_debtor(debtor_data, data.get('payment', {}))
        
        self._select_new_debtor_in_order(debtor_data)
    
    def _search_existing_debtor(self, debtor_data: dict) -> bool:
        """Search for existing Debtor in Fakturama"""
        logger.info("Searching for existing Debtor")
        
        try:
            search_icon = self.uia.window.ButtonControl(Name="Select existing contact")
            search_icon.Click()
        except:
            address_panel = self.uia.window.PaneControl(Name="Addresses")
            if address_panel.Exists(1):
                icons = address_panel.GetChildren()
                for icon in icons:
                    if "contact" in str(icon.GetName()).lower():
                        icon.Click()
                        break
        
        time.sleep(0.5)
        
        select_dialog = self.uia.window.WindowControl(Name="Select the address")
        if not select_dialog.Exists(Config.ELEMENT_TIMEOUT):
            logger.warning("Could not open address selector")
            return False
        
        search_field = select_dialog.EditControl(AutomationId="searchField")
        if search_field.Exists(1):
            search_field.SetValue(debtor_data.get('company', ''))
            time.sleep(0.5)
        else:
            select_dialog.FindControl(Name="Search").SetValue(debtor_data.get('company', ''))
            time.sleep(0.5)
        
        results_list = select_dialog.ListControl()
        if results_list.Exists(1):
            items = results_list.GetChildren()
            if len(items) == 1:
                item = items[0]
                if self._verify_debtor_match(item, debtor_data):
                    item.Click()
                    self.uia.click_element(Name="OK", ControlType="Button", window=select_dialog)
                    logger.success("Found exact Debtor match")
                    return True
                else:
                    logger.warning("Single result but doesn't match extracted data")
            elif len(items) > 1:
                for item in items:
                    if self._verify_debtor_match(item, debtor_data):
                        item.Click()
                        self.uia.click_element(Name="OK", ControlType="Button", window=select_dialog)
                        logger.success("Found exact Debtor match")
                        return True
                
                logger.warning("Multiple results but none match exactly")
        
        self.uia.click_element(Name="Cancel", ControlType="Button", window=select_dialog)
        return False
    
    def _verify_debtor_match(self, list_item, debtor_data: dict) -> bool:
        """Verify list item matches extracted debtor data"""
        item_text = list_item.GetValue()
        
        matches = True
        for field in ['company', 'first_name', 'last_name', 'zip', 'city']:
            if debtor_data.get(field):
                if debtor_data[field].lower() not in item_text.lower():
                    matches = False
                    break
        
        return matches
    
    def _create_new_debtor(self, debtor_data: dict, payment_data: dict):
        """Create new Debtor in Fakturama"""
        logger.info("Creating new Debtor")
        
        self.uia.click_element(Name="New contact", ControlType="Button")
        time.sleep(0.5)
        
        self.debtor_window = self.uia.window.WindowControl(Name="New Debtor")
        if not self.debtor_window.Exists(Config.ELEMENT_TIMEOUT):
            self.debtor_window = self.uia.window.WindowControl(Name="Debtor")
        
        if not self.debtor_window.Exists(Config.ELEMENT_TIMEOUT):
            raise Exception("Could not open Debtor editor")
        
        self._fill_debtor_fields(debtor_data)
        
        self._fill_debtor_address(debtor_data)
        
        self._set_debtor_misc(debtor_data)
        
        self._set_debtor_payment(payment_data)
        
        self.uia.click_element(Name="Save", ControlType="Button", window=self.debtor_window)
        time.sleep(1)
        
        self.uia.click_element(Name="Close", ControlType="Button", window=self.debtor_window)
        time.sleep(0.5)
        
        logger.success("New Debtor created")
    
    def _fill_debtor_fields(self, debtor_data: dict):
        """Fill basic Debtor fields"""

        if debtor_data.get('company'):
            company_field = self.debtor_window.EditControl(Name="Company")
            company_field.SetValue(debtor_data['company'])
        
        if debtor_data.get('first_name'):
            first_name_field = self.debtor_window.EditControl(Name="First name")
            first_name_field.SetValue(debtor_data['first_name'])
        
        if debtor_data.get('last_name'):
            last_name_field = self.debtor_window.EditControl(Name="Name")
            last_name_field.SetValue(debtor_data['last_name'])
            
    def _fill_debtor_address(self, debtor_data: dict):
        """Fill Debtor address"""
        addresses_tab = self.debtor_window.TabControl(Name="Addresses")
        addresses_tab.Click()
        time.sleep(0.2)
        
        if debtor_data.get('street'):
            self.debtor_window.EditControl(Name="Street").SetValue(debtor_data['street'])
        
        if debtor_data.get('zip'):
            self.debtor_window.EditControl(Name="ZIP").SetValue(debtor_data['zip'])
        
        if debtor_data.get('city'):
            self.debtor_window.EditControl(Name="City").SetValue(debtor_data['city'])
        
        if debtor_data.get('country'):
            country_combo = self.debtor_window.ComboBoxControl(Name="Country")
            country_combo.SetValue(debtor_data['country'])
        
        if debtor_data.get('email'):
            self.debtor_window.EditControl(Name="E-Mail").SetValue(debtor_data['email'])
        
        if debtor_data.get('phone'):
            self.debtor_window.EditControl(Name="Telephone").SetValue(debtor_data['phone'])
        
        roles_list = self.debtor_window.ListControl(Name="Addresses")
        invoice_role = roles_list.ListItemControl(Name="Invoice address")
        if invoice_role.Exists(1):
            invoice_role.Click()
            checkbox = roles_list.CheckBoxControl()
            checkbox.SetValue(True)
        
        delivery_role = roles_list.ListItemControl(Name="Delivery address")
        if delivery_role.Exists(1):
            delivery_role.Click()
            checkbox = roles_list.CheckBoxControl()
            checkbox.SetValue(True)
    
    def _set_debtor_misc(self, debtor_data: dict):
        """Set Miscellaneous fields"""
        misc_tab = self.debtor_window.TabControl(Name="Miscellaneous")
        misc_tab.Click()
        time.sleep(0.2)
        
        if debtor_data.get('alias'):
            self.debtor_window.EditControl(Name="Alias name").SetValue(debtor_data['alias'])
        
        discount_field = self.debtor_window.EditControl(Name="Discount")
        discount_field.SetValue("0")
        
        net_gross_combo = self.debtor_window.ComboBoxControl(Name="Net or Gross")
        net_gross_combo.SetValue("Net")
    
    def _set_debtor_payment(self, payment_data: dict):
        """Set Payment Method for Debtor"""
        payment_tab = self.debtor_window.TabControl(Name="Payment")
        payment_tab.Click()
        time.sleep(0.2)
        
        payment_method = payment_data.get('method')
        if not payment_method:
            logger.warning("No payment method extracted")
            return
        
        method_combo = self.debtor_window.ComboBoxControl(Name="Payment method")
        method_combo.Click()
        
        method_items = method_combo.GetChildren()
        found = False
        for item in method_items:
            if payment_method.lower() in item.GetName().lower():
                item.Click()
                found = True
                break
        
        if not found:
            logger.info(f"Creating new payment method: {payment_method}")
            self._create_payment_method(payment_method)
            method_combo.Click()
            time.sleep(0.5)
            new_item = method_combo.ListItemControl(Name=payment_method)
            if new_item.Exists(1):
                new_item.Click()
    
    def _create_payment_method(self, method_name: str):
        """Create new Payment Method"""
        self.uia.click_element(Name="Data", ControlType="MenuItem")
        time.sleep(0.2)
        self.uia.click_element(Name="Terms of payment", ControlType="MenuItem")
        time.sleep(0.5)
        
        terms_dialog = self.uia.window.WindowControl(Name="Terms of payment")
        if not terms_dialog.Exists(Config.ELEMENT_TIMEOUT):
            logger.warning("Could not open Terms of payment")
            return
        
        self.uia.click_element(Name="New", ControlType="Button", window=terms_dialog)
        time.sleep(0.3)
        
        name_field = terms_dialog.EditControl(Name="Name")
        name_field.SetValue(method_name)
        
        desc_field = terms_dialog.EditControl(Name="Description")
        desc_field.SetValue(method_name)
        
        code_combo = terms_dialog.ComboBoxControl(Name="Payment code")
        code_mapped = Config.PAYMENT_CODE_MAP.get(method_name, method_name)
        code_combo.SetValue(code_mapped)
        
        cash_discount = terms_dialog.EditControl(Name="Cash discount")
        cash_discount.SetValue("0")
        
        discount_days = terms_dialog.EditControl(Name="Discount Days")
        discount_days.SetValue("0")
        
        net_days = terms_dialog.EditControl(Name="Net Days")
        net_days.SetValue("0")
        
        self.uia.click_element(Name="Save", ControlType="Button", window=terms_dialog)
        time.sleep(0.5)
        
        self.uia.click_element(Name="Close", ControlType="Button", window=terms_dialog)
        time.sleep(0.3)
        
        logger.success(f"Created payment method: {method_name}")
    
    def _select_new_debtor_in_order(self, debtor_data: dict):
        """Return to Order and select the newly created Debtor"""
        logger.info("Selecting new Debtor in Order")
        
        self.uia.window.WindowControl(Name="Order").SetFocus()
        time.sleep(0.5)
        
        self._search_existing_debtor(debtor_data)
        
        logger.success("New Debtor selected in Order")