
from component_repo import IComponentProvider
from pydantic import ValidationError, BaseModel, Field
import logging
import streamlit as st
from scraipe.extended import TelegramMessageScraper
import os
import qrcode
import streamlit as st

class TelegramSchema(BaseModel):
    api_id: str = Field(
        ..., description="API ID from Telegram")
    api_hash: str = Field(
        ..., description="API Hash from Telegram",
        st_kwargs_type="password")
    phone_number: str = Field(..., description="Phone number for Telegram account")
    password:str = Field(
        ..., description="Password for Telegram account",
        st_kwargs_type="password")
        
class TelegramComponentProvider(IComponentProvider):
    def get_config_schema(self):
        return TelegramSchema
    
    def get_default_config(self):
        # Try to populate with environment variables
        return TelegramSchema(
            api_id=os.getenv("TELEGRAM_API_ID", ""),
            api_hash=os.getenv("TELEGRAM_API_HASH", ""),
            phone_number=os.getenv("TELEGRAM_PHONE_NUMBER", ""),
            password=os.getenv("TELEGRAM_PASSWORD", ""),
        )
    
    def get_component(self, config):    
        try:
            # Validate the config against the schema
            validated_config = TelegramSchema(**config.model_dump())
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e
        
        try:
            # Create an instance of the target class with the validated config
            component = TelegramMessageScraper(**config.model_dump(), sync_auth=False, use_qr_login=True)
            logging.warning("Created a new component instance.")
        except Exception as e:
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
        
        @st.dialog("QR Code")
        def qr_dialog():
            st.image(buf.getvalue(), caption="Scan this QR code with your Telegram app.")     
        qr_dialog()   
        
        component:TelegramMessageScraper
        if component is None:
            st.warning("Failed to create component instance.")
            return None
        return component