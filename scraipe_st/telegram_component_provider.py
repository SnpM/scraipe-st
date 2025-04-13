
from component_repo import IComponentProvider, ComponentStatus
from pydantic import ValidationError, BaseModel, Field
import logging
import streamlit as st
from scraipe.extended import TelegramMessageScraper
from scraipe.extended.telegram_message_scraper import AuthState, QrLoginContext
import os
import qrcode
import streamlit as st
import time
from threading import Event
from streamlit.runtime.scriptrunner import get_script_run_ctx

class TelegramSchema(BaseModel):
    api_id: str = Field(
        ..., description="API ID from https://my.telegram.org/apps")
    api_hash: str = Field(
        ..., description="API Hash from https://my.telegram.org/apps",
        st_kwargs_type="password")
    password:str = Field(
        ..., description="Password for Telegram account. Only required if 2FA is enabled.",
        st_kwargs_type="password", st_kwargs_placeholder="Leave blank if not using 2FA.")
        
class TelegramComponentProvider(IComponentProvider):
    is_logging_in:Event

    def __init__(self):
        self.is_logging_in = None
        self.qr_cont = None
        self.auth_state_ref = None
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
        if component.is_authenticating():
            return ComponentStatus.DELAYED
        return ComponentStatus.FAILED

    def get_component(self, config):
        try:
            # Validate the config against the schema
            validated_config = TelegramSchema(**config.model_dump())
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise e
        try:
            self.is_logging_in = Event()
            self.is_logging_in.set()
            self.auth_state_ref = [None]
            run_context = get_script_run_ctx()
            
            def handle_login_done(auth_state:AuthState):
                self.is_logging_in.clear()
                self.auth_state_ref[0] = auth_state
                    
            # Create an instance of the target class with the validated config
            component = TelegramMessageScraper(**config.model_dump(), sync_auth=False)
            # Subscribe to the login event
            login_context:QrLoginContext = component.login_context
            login_context.subscribe_done(handle_login_done)
        except Exception as e:
            logging.error(f"Failed to create component instance: {e}")
            raise Exception("Failed to create component instance:",e) from e

        self.qr_cont = st.empty()
        component:TelegramMessageScraper
        if component is None:
            st.warning("Failed to create component instance.")
            return None
        return component
            
    
    def late_update(self, component):
        if self.is_logging_in is not None and self.is_logging_in.is_set():
            # Note: usage of qr_cont assumes that late_update will be called in same execution as get_component()
            # login_cont = self.qr_cont.status(label="Logging in...")
            
            parent_cont = st.empty()
            login_cont = parent_cont.status(label="Logging in...",expanded=True)
            with login_cont:
                # Display qrcode in popup
                login_context = component.login_context
                url = login_context.get_qr_url()
                qr = qrcode.QRCode()
                qr.add_data(url)
                qr.make(fit=True)
                from io import BytesIO
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf)
                st.image(buf, caption="Scan this QR code with your Telegram app.")    
                def on_cancel():
                    self.is_logging_in.clear()
                    st.session_state["login_cancel"] = True
                st.button("Cancel", on_click=on_cancel) 
                
                acc = 0
                POLL_INTERVAL = .4
                while True:
                    # Block until login completes
                    st.write
                    if not self.is_logging_in.is_set():
                        # print("Login over, calling st.rerun()")
                        # st.rerun(scope="app")
                        break
                    time.sleep(POLL_INTERVAL)
                    acc
                        
            assert self.auth_state_ref[0] is not None
            auth_state = self.auth_state_ref[0]
            parent_cont.empty()