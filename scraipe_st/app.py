import streamlit as st
from component_repo import ComponentRepo, ComponentMetadata, IComponentProvider
from streamlit_scroll_navigation import scroll_navbar
from utils import label2anchor
import pandas as pd
from default_config import get_default_links, register_default_components
from scraipe import Workflow

from utils import get_random_wikipedia_links

# Monkey patch to fix import issue. Hopefully nothing breaks
from pydantic_settings import BaseSettings
import pydantic
setattr(pydantic, "BaseSettings", BaseSettings)
import streamlit_pydantic as sp

class App:
    nav_pairs = [
        ("Links", "Edit Links"),
        ("Scraper", "Configure Scraper"),
        ("Analyzer", "Configure Analyzer"),
        ("Workflow", "Run Workflow"),]
    nav_labels = [pair[0] for pair in nav_pairs]
    nav_anchors = [label2anchor(pair[1]) for pair in nav_pairs]
    version:str

    def __init__(self, title: str ="Scraipe", version: str = "demo v0.1.0"):
        self.title = title
        self.version = version
        
        self.component_repo = ComponentRepo()
        register_default_components(self.component_repo)
        
    def get_workflow(self, scraper=None, analyzer=None) -> Workflow:
        """
        Get the workflow object from the session state.
        
        Returns:
            Workflow: The workflow object.
        """
        if "workflow" not in st.session_state:
            st.session_state["workflow"] = Workflow(scraper, analyzer)
        workflow = st.session_state["workflow"]
        if scraper is not None:
            workflow.scraper = scraper
        if analyzer is not None:
            workflow.analyzer = analyzer
        return workflow

    def main(self):
        st.set_page_config(
            page_title=self.title,
            page_icon=":mag_right:",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        #===Sidebar and Title===
        with st.sidebar:
            st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{self.title}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;'>{self.version}</h3>", unsafe_allow_html=True)
            st.divider()
            scroll_navbar(self.nav_anchors, anchor_labels=self.nav_labels)
            
        #===Links===
        st.subheader("Edit Links")

        uploaded_file = st.file_uploader(
            "Choose a csv, txt, or Excel file", type=["csv","xlsx","xls","txt"],
            accept_multiple_files=False,
        )
    
        
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                st.session_state["links_df"] = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith((".xlsx", ".xls")):
                st.session_state["links_df"] = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith(".txt"):
                st.session_state["links_df"] = pd.read_csv(uploaded_file, sep="\t")
            else:
                st.error("Unsupported file type. Please upload a csv, txt, or Excel file.")    
                            
            # Validate the dataframe has a 'links' column case insensitive
            if links_df := st.session_state.get("links_df") is not None:
                if "link" not in links_df.columns:
                    st.error("The uploaded file must contain URL links in the 'link' column")
                    st.session_state["links_df"] = None
                    uploaded_file = None
                else:
                    st.session_state["links_df"] = links_df["link"].dropna().reset_index(drop=True)
        
      
        # Set default links if no file is uploaded
        if st.session_state.get("links_df") is None:
            st.session_state["links_df"] = pd.DataFrame(
                data={
                    'link': get_default_links()
                }
            )
        
        with st.expander("Edit", expanded=True):
            column_config = {
                "link": st.column_config.LinkColumn("link"),
            }
            edited_links = st.data_editor(
                st.session_state["links_df"], num_rows="dynamic",
                use_container_width=True,hide_index=False,
                column_config=column_config,
                
            )
            

            if (st.button("Generate 10 Links", key="generate_links", help="Generate links from Wikipedia")):
                links = get_random_wikipedia_links(10)
                # append links to the dataframe. If dataframe has extra columns, just set to null
                new_links_df = pd.DataFrame(
                    data={
                        'link': links
                    }
                )
                # Check if the dataframe has extra columns
                if len(st.session_state["links_df"].columns) > 1:
                    for col in st.session_state["links_df"].columns[1:]:
                        new_links_df[col] = None
                st.session_state["links_df"] = pd.concat([st.session_state["links_df"], new_links_df], ignore_index=True)
                st.rerun()
                
            
        st.divider()
        
        #===Scrapers===

        ## Display the selected scraper's metadata
        def configure_component_loop(comp:str, provider_options:list):
            st.subheader(f"Configure {comp}")
        
            # Select a scraper from the component repository
            selected_option = st.selectbox(f"Select {comp}", provider_options, format_func=lambda x: x[1].name, key=f"select_{comp}")
            if selected_option is not None:
                metadata:ComponentMetadata = selected_option[1]
                comp_key = f"{comp}_{metadata.name}"
                

                provider:IComponentProvider = selected_option[0]
                    
                description_holder = st.empty()
                # Configure the selected scraper
                schema = provider.get_config_schema()
                config_key = f"config_{comp_key}"
                config = st.session_state.get(config_key, None)
                
                                
                if schema:
                    config = sp.pydantic_form(f"{comp_key}_form", config or provider.get_default_config() or schema, submit_label="Create",)        
                    if config is not None:
                        try:
                            st.session_state[comp_key] = provider.get_component(config)                            
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            st.error(f"Error creating {comp}: {e}")
                            st.session_state[comp_key] = None
                        else:
                            st.session_state[config_key] = config

                else:
                    if st.session_state.get(comp_key) is None:
                        st.session_state[comp_key] = provider.get_component(None)
                
                # Add green checkmark if the component is good config
                instance = st.session_state.get(comp_key, None)
                description_str = f"**{metadata.name}**: {metadata.description}"
                if instance is not None:
                    description_str = "✔️" + description_str
                else:
                    description_str = "⚠️" + description_str
                description_holder.markdown(description_str)
                
                return comp_key
        scraper_key = configure_component_loop("Scraper", self.component_repo.get_scrapers())
        st.divider()
        
        #===Analyzers===
        analyzer_key = configure_component_loop("Analyzer", self.component_repo.get_analyzers())
        st.divider()
        
        
        #===Workflow===
        st.subheader("Run Workflow")
        def run_scrape_section():
            scraper = st.session_state.get(scraper_key)
            workflow = self.get_workflow(scraper=scraper)
            if scraper is None:
                st.warning("Please configure a good scraper to scrape links.")
            else:
                if st.button("Scrape"):
                    links_df = st.session_state.get("links_df")
                    links = links_df["link"].tolist()
                    bar = st.progress(0.0, text="Scraping...")
                    progress_delta = 1.0/len(links)
                    for result in workflow.scrape_generator(links, overwrite=True):
                        bar.progress(progress_delta, text=f"Scraping {len(links)} links...")
                    bar.empty()
            scrapes_df = workflow.get_scrapes()
            if "metadata" in scrapes_df.columns:
                scrapes_df = scrapes_df.drop(columns=["metadata"])
            if scrapes_df is not None and len(scrapes_df) > 0:
                column_config = {
                    "link": st.column_config.LinkColumn("Link", width="medium"),
                    "content": st.column_config.TextColumn("Content", width="large"),
                    "scrape_success": st.column_config.CheckboxColumn("Success",width="small"),
                    "scrape_error": st.column_config.TextColumn("Error", width="small"),
                }
                st.dataframe(scrapes_df, use_container_width=True,
                    hide_index=True,
                    column_config=column_config,
                )
        run_scrape_section()
        
        st.divider()
                
        def run_analyze_section():
            analyzer = st.session_state.get(analyzer_key)
            workflow = self.get_workflow(analyzer=analyzer)
            
            if analyzer is None:
                st.warning("Please configure a good analyzer to analyze content.")
            else:
                scrapes_df = workflow.get_scrapes()
                if st.button("Analyze"):
                    bar = st.progress(0.0, text="Analyzing...")
                    scrapes_length = len(scrapes_df) if scrapes_df is not None else 0
                    progress_delta = 1.0/scrapes_length if scrapes_length > 0 else 1.0
                    for result in workflow.analyze_generator(overwrite=True):
                        bar.progress(progress_delta, text=f"Analyzing {scrapes_length} content items....")
                    bar.empty()
            analysis_df = workflow.get_analyses()
            if analysis_df is not None and len(analysis_df) > 0:
                # Check for analysis_success column
                if "analysis_success" in analysis_df.columns:
                    column_config = {
                        "output": st.column_config.JsonColumn("Output", width="large"),
                        "link": st.column_config.LinkColumn("Link", width="medium"),
                        "analysis_success": st.column_config.CheckboxColumn("Success",width="small"),
                        "analysis_error": st.column_config.TextColumn("Error", width="small"),
                    }
                    st.dataframe(analysis_df, use_container_width=True,
                        hide_index=True,
                        column_config=column_config,
                    )
        run_analyze_section()
            
def serve():
    """
    Serve the Streamlit app.
    
    Returns:
        None
    """
    app = App()
    app.main()
if __name__ == "__main__":
    serve()