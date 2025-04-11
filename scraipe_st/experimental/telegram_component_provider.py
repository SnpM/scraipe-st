# NOTE: auth is not currently working

from component_repo import IComponentProvider
from pydantic import ValidationError, BaseModel
import logging
import streamlit as st


class TelegramSchema(BaseModel):
    api_id: str
    api_hash: str
    phone_number: str
    auth_code: str
    password:str
        
class TelegramComponentProvider(IComponentProvider):
    def get_config_schema(self):
        return TelegramSchema
    
    def get_component(self, config):
        def get_init_params(conf):
            dump = conf.model_dump()
            del dump["auth_code"]
            return dump
        
        # for testing
        config = TelegramSchema(
            api_id = "29044868",
            api_hash = "bbd25e6b50d1ca4f5c27754f51d8dc95",
            phone_number = "18328467889",
            auth_code = config.auth_code,
            password=""
        )
        SESSION_KEY = "instance"
        if st.session_state.get(SESSION_KEY) is None:
            try:
                # Validate the config against the schema
                validated_config = TelegramSchema(**config.model_dump())
            except ValidationError as e:
                logging.error(f"Validation error: {e}")
                raise e
            
            try:
                
                # Create an instance of the target class with the validated config
                component = TelegramMessageScraper(**get_init_params(config), sync_auth=False)
                logging.warning("Created a new component instance.")
            except Exception as e:
                raise Exception("Failed to create component instance:",e) from e
            
            if config.auth_code:
                logging.warning("Ignoring stale auth code.")
                config.auth_code = None
                
            st.session_state[SESSION_KEY] = component
        
        # auth phase 2
        component:TelegramMessageScraper = st.session_state.get(SESSION_KEY)
        
        if component.is_authenticated():
            logging.info("Component is already authenticated.")
            return component
        else:
            # Prompt user for authentication
            if config.auth_code:
                try:
                    # Attempt to sign into Telegram
                    component.sign_in(config.auth_code)
                    print(config.auth_code)
                    st.success("Successfully authenticated!")
                except Exception as e:
                    logging.error(f"Authentication error: {e}")
                    st.error(str(e))
                # Reset session variable
                print("deleting session state")
                del st.session_state[SESSION_KEY]
            else:
                st.warning("Auth code is required. Check your Telegram app.")
            return None