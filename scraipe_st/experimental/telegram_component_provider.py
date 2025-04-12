
from component_repo import IComponentProvider, ComponentStatus
from pydantic import ValidationError, BaseModel, Field
import logging
import streamlit as st
from scraipe.extended import TelegramMessageScraper
from scraipe.extended.telegram_message_scraper import AuthPhase
import os
import qrcode
import streamlit as st
import time
from threading import Event

class TelegramSchema(BaseModel):
    api_id: str = Field(
        ..., description="API ID from Telegram")
    api_hash: str = Field(
        ..., description="API Hash from Telegram",
        st_kwargs_type="password")
    password:str = Field(
        ..., description="Password for Telegram account",
        st_kwargs_type="password")
        
class TelegramComponentProvider(IComponentProvider):
    is_logging_in:Event

    def __init__(self):
        self.is_logging_in = Event()
    def get_config_schema(self):
        return TelegramSchema
    
    def get_default_config(self):
        # Try to populate with environment variables
        return TelegramSchema(
            api_id=os.getenv("TELEGRAM_API_ID", ""),
            api_hash=os.getenv("TELEGRAM_API_HASH", ""),
            password=os.getenv("TELEGRAM_PASSWORD", ""),
        )
        
    def get_component_status(self, component:TelegramMessageScraper):
        if component is None:
            return ComponentStatus.FAILED
        if component.is_authenticated():
            return ComponentStatus.READY
        if component.is_monitoring_qr():
            return ComponentStatus.DELAYED
        return ComponentStatus.FAILED
    @st.dialog("QR Code")
    def qr_dialog(self, img):
        st.image(img, caption="Scan this QR code with your Telegram app.")
        print("fdsa")
    def get_component(self, config):
        
        try:
            # Validate the config against the schema
            validated_config = TelegramSchema(**config.model_dump())
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e
        
        print("asdf")
        try:
            self.is_logging_in.set()
            print("set")
            def handle_login_done(auth_phase:AuthPhase):
                print("cleared")
                self.is_logging_in.clear()
                    
            # Create an instance of the target class with the validated config
            component = TelegramMessageScraper(**config.model_dump(), sync_auth=False, use_qr_login=True)
            # Subscribe to the login event
            component.subscribe_qr_login_listener(handle_login_done)
        except Exception as e:
            logging.error(f"Failed to create component instance: {e}")
            raise Exception("Failed to create component instance:",e) from e
        
        #===auth phase 2===
        
        # Display qrcode in popup
        url = component.get_qr_url()
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.make(fit=True)
        from io import BytesIO
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf)
        
        if self.is_logging_in.is_set():              
            # this should spawn in different execution context
            self.qr_dialog(buf.getvalue())  
            print("after qr dialog")
        
        component:TelegramMessageScraper
        if component is None:
            st.warning("Failed to create component instance.")
            return None
        return component
    
    def late_update(self, component):
        if self.is_logging_in.is_set():
            while True:
                print("blocked")
                # Block until login completes
                if not self.is_logging_in.is_set():
                    print("rerunning")
                    st.rerun(scope="app")
                    break
                time.sleep(.4)