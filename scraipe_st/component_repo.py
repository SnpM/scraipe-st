from typing import final, Tuple, Dict, Any, Type, Protocol, Union, TypeVar
from scraipe.classes import IScraper, IAnalyzer
from collections import OrderedDict
from pydantic import BaseModel, ValidationError
import logging
from abc import ABC, abstractmethod
from enum import Enum

class ComponentMetadata:
    """
    A class that contains information about a component.
    """
    def __init__(self, name:str = None, description:str = None):
        self.name = name
        self.description = description
    
class ComponentStatus(Enum):
    READY = 1
    DELAYED = 0
    FAILED = -1
    
class IComponentProvider():
    """
    A class that contains the component configuration blueprint for the UI.
    """
    @abstractmethod
    def get_config_schema(self) -> Type[BaseModel]:
        """
        Get the configuration model.
        
        Returns:
            Type[BaseModel]: The configuration model class.
        """
        ...
    
    @abstractmethod
    def get_component(self, config:BaseModel) -> Any:
        """
        Get the component instance based on the configuration.
        
        Returns:
            Any: The component instance.
        """
        ...
        
    def get_component_status(self, component) -> ComponentStatus:
        """
        Get the status of the component.
        
        Returns:
            ComponentStatus: The status of the component.
        """
        if component is not None:
            return ComponentStatus.READY
        return ComponentStatus.FAILED
    
    def get_default_config(self) -> BaseModel:
        """
        Get the default configuration.
        
        Returns:
            BaseModel: The default configuration instance.
        """
        return None
    
    def late_update(self, component:Any) -> None:
        """
        Run logic at the end of app's configuration loop.
        
        Args:
            component (Any): The component instance.
        """
        pass
        
class ProvidedComponent(IComponentProvider):
    """The component is already instantiated and can be used without additional configuration."""
    def __init__(self, component:Any):
        self.component = component
    def get_config_schema(self):
        return None
    def get_component(self, config:BaseModel) -> Any:
        return self.component
    def get_default_component(self):
        return self.get_component(None)
    
class ComponentRepo:
    registered_scrapers:Dict[str,Tuple[IComponentProvider,ComponentMetadata]]
    registered_analyzers:Dict[str,Tuple[IComponentProvider,ComponentMetadata]]
    
    def __init__(self):
        """
        Initialize the component repository.
        """
        self.registered_scrapers = OrderedDict()
        self.registered_analyzers = OrderedDict()
    
    
    def get_unique_name(self, name:str, repo:dict[str,Any]) -> str:
        """
        Get a unique name for a scraper.
        """
        if name not in repo:
            return name
        
        import re
        id_suffix = re.search(r"_(\d+)$", name)
        id = 0
        if id_suffix:
            id = int(id_suffix.group(1))
            name = name[:id_suffix.start()]
            
        if name in repo:
            # Linear search for a unique name
            for i in range(id + 1, 100):
                new_name = f"{name}_{i}"
                if new_name not in repo:
                    return new_name
        raise ValueError(f"Could not find a unique name for {name}.")
    
    def _register(self,
        provider:IComponentProvider,
        metadata:ComponentMetadata,
        repo:Dict[str,Tuple[Any, ComponentMetadata]]) -> str:
        """
        Register a component to the component repository.
        
        Returns:
            str: The unique name of the registered component.
        """
        assert isinstance(provider, IComponentProvider), "The provider must implement IComponentProvider"
        if metadata.name is None:
            metadata.name = provider.__class__.__name__
        metadata.name = self.get_unique_name(metadata.name, repo)
        
        repo[metadata.name] = (provider, metadata)
        return metadata.name
    
    def register_scraper(self,
        scraper:IScraper|IComponentProvider,
        metadata:ComponentMetadata) -> str:
        """
        Register a scraper to the component repository.
        
        Returns:
            str: The unique name of the registered scraper.
        """
        if isinstance(scraper, IScraper):
            # Wrap the scraper in a ProvidedComponent
            scraper = ProvidedComponent(scraper)
        elif not isinstance(scraper, IComponentProvider):
            raise ValueError("The scraper must be an instance of IScraper or IComponentProvider")
        return self._register(scraper, metadata, self.registered_scrapers)
    
    def register_analyzer(self,
        analyzer:IAnalyzer|IComponentProvider,
        metadata:ComponentMetadata = None) -> str:
        """
        Register an analyzer to the component repository.
        
        Returns:
            str: The unique name of the registered analyzer.
        """
        if isinstance(analyzer, IAnalyzer):
            # Wrap the analyzer in a ProvidedComponent
            analyzer = ProvidedComponent(analyzer)
        elif not isinstance(analyzer, IComponentProvider):
            raise ValueError("The analyzer must be an instance of IAnalyzer or IComponentProvider")
        return self._register(analyzer, metadata, self.registered_analyzers)
    
    def get_scrapers(self):
        """
        Get a list of registered scrapers in the order they were registered.
        
        Returns:
            list: A list of registered scrapers.
        """
        return list(self.registered_scrapers.values())
    
    def get_analyzers(self):
        """
        Get a list of registered analyzers in the order they were registered.
        
        Returns:
            list: A list of registered analyzers.
        """
        return list(self.registered_analyzers.values())