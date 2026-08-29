import time
import uiautomation as uia
import pyautogui
import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from src.config import Config
from src.utils.logger import capture_screenshot


class UIAController:
    def __init__(self):
        self.window = None
        self.timeout = Config.ELEMENT_TIMEOUT
        self.retry_count = Config.RETRY_COUNT
        
    def connect_to_fakturama(self):
        """Connect to Fakturama window"""
        logger.info("Connecting to Fakturama")
        
        for attempt in range(self.retry_count):
            try:
                self.window = uia.WindowControl(
                    Name=Config.FAKTURAMA_WINDOW_TITLE,
                    searchDepth=1,
                    waitTime=self.timeout
                )
                
                if self.window.Exists(0):
                    self.window.SetFocus()
                    logger.success("Connected to Fakturama")
                    return
                
            except:
                logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(Config.RETRY_DELAY)
        
        raise Exception("Could not connect to Fakturama")
    
    def find_element(self, **kwargs):
        """Find UI element with retry logic"""
        for attempt in range(self.retry_count):
            try:
                element = self.window.Control(**kwargs)
                if element.Exists(0):
                    return element
                else:
                    logger.debug(f"Element not found: {kwargs}")
                    time.sleep(0.5)
            except Exception as e:
                logger.debug(f"Find element attempt {attempt + 1} failed: {e}")
                time.sleep(Config.RETRY_DELAY)
        
        capture_screenshot("element_not_found")
        raise Exception(f"Element not found: {kwargs}")
    
    def click_element(self, **kwargs):
        """Click on UI element"""
        element = self.find_element(**kwargs)
        
        element.WaitForEnabled(self.timeout)
        element.WaitForExist(self.timeout)
        
        element.Click()
        time.sleep(0.2)
        
    def set_text(self, text, **kwargs):
        """Set text in UI element"""
        element = self.find_element(**kwargs)
        
        element.WaitForEnabled(self.timeout)
        
        element.SetValue(text)
        time.sleep(0.1)
        
    def get_text(self, **kwargs) -> str:
        """Get text from UI element"""
        element = self.find_element(**kwargs)
        return element.GetValue()
    
    def select_combobox_item(self, item_text, **kwargs):
        """Select item from combobox"""
        element = self.find_element(**kwargs)
        
        combobox = element if element.ControlType == uia.ControlType.ComboBox else element.ComboBox()
        combobox.WaitForEnabled(self.timeout)
        combobox.Click()
        
        list_item = combobox.ListItemControl(Name=item_text)
        if list_item.Exists(self.timeout):
            list_item.Click()
        else:
            raise Exception(f"List item not found: {item_text}")
        
        time.sleep(0.1)
    
    def wait_for_dialog(self, dialog_name: str) -> bool:
        """Wait for dialog to appear"""
        dialog = self.window.WindowControl(Name=dialog_name)
        return dialog.Exists(self.timeout)
    
    def capture_screenshot(self, name: str = "screenshot"):
        """Capture screenshot for debugging"""
        capture_screenshot(name)
    
    def search_using_icon(self, icon_type: str):
        """Click search icon (upper icon, not green +)"""
        
        panel = self.window.PaneControl(AutomationId="panelSearch")
        
        if icon_type == "debtor":
            icon = panel.ButtonControl(Name="Select existing contact")
        elif icon_type == "product":
            icon = panel.ButtonControl(Name="Select product")
        else:
            raise Exception(f"Unknown icon type: {icon_type}")
        
        icon.WaitForEnabled(self.timeout)
        icon.Click()
        time.sleep(0.5)
    
    def click_green_plus(self, location: str):
        """Click green + button to create new entity"""       
        if location == "debtor":
            button = self.window.ButtonControl(Name="New contact")
        elif location == "product":
            button = self.window.ButtonControl(Name="New product")
        elif location == "payment":
            button = self.window.ButtonControl(Name="New payment term")
        elif location == "vat":
            button = self.window.ButtonControl(Name="New VAT rate")
        else:
            raise Exception(f"Unknown location: {location}")
        
        button.WaitForEnabled(self.timeout)
        button.Click()
        time.sleep(0.5)