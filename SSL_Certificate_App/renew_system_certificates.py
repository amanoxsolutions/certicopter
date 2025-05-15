# Standard library imports
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Type

# Third-party imports
from ping3 import ping

# Local imports
from certbot_utils import create_final_certificate_zip
from certificatemanager_abc import CertificateManager
from nutanix_executor import NutanixCertificateManager
from rubrik_executor import RubrikCertificateManager
from hycu_executor import HYCUCertificateManager
from paloalto_executor import PaloAltoCertificateManager
from vamax_executor import VAMaxCertificateManager
from vsphere_executor import VSphereCertificateManager
from config_manager import (
    load_configuration_file,
    get_provider_instances,
    get_certificate_manager_class,
    get_instance_config
)

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("renew_system_certificates")

# Renew SSL certificates for all specified providers and their instances
def renew_provider_certificates(
    included_providers: Optional[List[str]], 
    excluded_providers: Optional[List[str]], 
    config_file_path: str
) -> None:

    logger.info("Configuration file is getting loaded")
    config = load_configuration_file(config_file_path=config_file_path)
    logger.debug("Configuration file was loaded successfully")

    # Download root certificate
    try:
        os.system("wget https://letsencrypt.org/certs/isrgrootx1.pem")
        logger.debug("Root certificate was downloaded successfully")
        logger.debug(f"Root certificate: {Path('isrgrootx1.pem').resolve()}")
    except Exception as e:
        logger.error(f"Failed to download root certificate: {str(e)}")
        raise

    # Get filtered provider instances
    filtered_providers = get_provider_instances(config, included_providers, excluded_providers)
    
    logger.info("Renewal process is being started")
    for provider, instances in filtered_providers.items():
        try:
            # Get certificate manager class
            certificate_manager_class_name = get_certificate_manager_class(provider)
            certificate_manager_class = globals()[certificate_manager_class_name]
            
            # Get required parameters for the provider
            required_provider_parameters = certificate_manager_class.get_required_parameters()
            
            # Process instances
            renew_instance_certificate(
                instances=instances,
                required_provider_parameters=required_provider_parameters,
                certificate_manager_class=certificate_manager_class
            )
            
        except Exception as e:
            logger.error(f"Failed to process provider {provider}: {str(e)}")
            continue

    # Create final zip file with all certificates
    zip_path = create_final_certificate_zip()

    if zip_path:
        logger.info(f"All certificates have been saved to {zip_path}")

# Renew certificates for a specific provider's instances
# Args: 
#     instances: Dictionary containing instance configurations
#     required_provider_parameters: List of required parameters for the provider
#     certificate_manager_class: The certificate manager class to use for renewal
def renew_instance_certificate(
    instances: Dict[str, Any],
    required_provider_parameters: List[str],
    certificate_manager_class: Type[CertificateManager]
) -> None:
    
    for instance in instances.get("instances", []):
        try:
            # Get instance configuration
            instance_config = get_instance_config(instance, required_provider_parameters)
            
            domain = instance_config.get("domain")
            if not domain:
                logger.error("Instance was skipped: domain is missing")
                continue
                
            logger.info(f"Domain for the instance is: {domain}")
            
            # Check connection
            if not check_instance_connection(domain):
                logger.error(f"Instance was skipped: Could not establish connection to {domain}")
                continue
                
            # Initialize and execute certificate renewal
            certificate_manager = certificate_manager_class(**instance_config)
            logger.info(f"Executing SSL certificate renewal for {domain}")
            certificate_manager.execute_certificate_renewal()

        except Exception as e:
            logger.error(f"Failed to process instance: {str(e)}")
            continue

def check_instance_connection(domain: str) -> bool:

    # Test connection to an instance by pinging its domain.
    try:
        response_time = ping(domain)
        if response_time is False:
            logger.warning(f"Ping to {domain} failed. This might be normal if ICMP is blocked.")
            return False
        return True
    except Exception as e:
        logger.error(f"Unexpected error while checking connection to {domain}: {str(e)}")
        return False