
# Standard library imports
from abc import ABC, abstractmethod

# Creating the CertificateManager object for managing the renewal of the SSL certificate

class CertificateManager(ABC):
    
    # Abstract base class that defines the structure for all providers.
    
    @staticmethod
    @abstractmethod
    def get_required_parameters() -> list:
        
        # Define which parameters the provider needs for the certificate renewal.
        
        pass

    @abstractmethod
    def __init__(self, domain, *args, **kwargs) -> None:
        self.domain = domain
        
        # Initialize the object with specific attributes.
        
        pass

    @abstractmethod
    def execute_certificate_renewal(self) -> None:
        
        # Execute certificate renewal for the instance of a provider through calling provider specific functions.
        
        pass

    @abstractmethod
    def post_new_certificate(self, *args, **kwargs) -> str:
        
        # There needs to be a post_new_certificate function to be sure that always a certificate is pushed to the instance.
        
        pass