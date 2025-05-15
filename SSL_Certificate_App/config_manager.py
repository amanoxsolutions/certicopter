# Standard library imports
import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("config_manager")

# Constants
DEFAULT_CERTIFICATE_FOLDER = "/home/appuser/certicopter"

# Global variables for certificate configuration
notification_email: Optional[str] = None
dns_plugin: Optional[str] = None
save_certificates: Optional[bool] = None

# Provider mappings
CERTIFICATE_MANAGER_MAP = {
    "nutanix": "NutanixCertificateManager",
    "rubrik": "RubrikCertificateManager",
    "hycu": "HYCUCertificateManager",
    "paloalto": "PaloAltoCertificateManager",
    "vamax": "VAMaxCertificateManager",
    "vsphere": "VSphereCertificateManager"
}

# DNS Plugin Mapping
DNS_PLUGIN_MAP = {
    "AWS (Route 53)": "dns-route53",
    "Cloudflare": "dns-cloudflare",
    "DigitalOcean": "dns-digitalocean",
    "GoDaddy": "dns-godaddy",
    "OVH": "dns-ovh",
    "DNSimple": "dns-dnsimple",
    "DNS Made Easy": "dns-dnsmadeeasy",
    "Gehirn": "dns-gehirn",
    "Google Cloud": "dns-google",
    "Linode": "dns-linode",
    "LuadDNS": "dns-luadns",
    "IBM NS1": "dns-nsone",
    "Sakura Cloud": "dns-sakuracloud"
}

def load_configuration_file(config_file_path: str) -> Dict[str, Any]:

    # Load and validate the configuration file.
    # Also sets up global configuration variables.
    try:
        path = Path(config_file_path)

        if path.suffix != ".json":
            logger.error(f"Only .json files are allowed! You provided {config_file_path}, which is not a .json file.")
            raise ValueError("Invalid file extension")
        
        # Read the file content using pathlib
        file_content = path.read_text()
        config = json.loads(file_content)

        # Validate and set global configuration
        validate_and_set_global_config(config)
        
        return config

    except FileNotFoundError:
        logger.error(f"File not found: {config_file_path}", exc_info=True)
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_file_path}")
        raise

def validate_and_set_global_config(config: Dict[str, Any]) -> None:

    # Validate and set global configuration variables.
    global notification_email, dns_plugin, save_certificates
    
    # Validate required global settings
    required_settings = ['hosting_provider', 'notification_email', 'save_certificates']
    for setting in required_settings:
        if setting not in config.get('certicopter_global_settings', {}):
            raise ValueError(f"Missing required global setting: {setting}")
    
    # Set global variables
    notification_email = config["certicopter_global_settings"]["notification_email"]
    logger.debug(f"Notification email: {notification_email}")
    hosting_provider = config["certicopter_global_settings"]["hosting_provider"]
    logger.debug(f"Hosting provider: {hosting_provider}")
    save_certificates = config["certicopter_global_settings"]["save_certificates"]
    logger.debug(f"Save certificates: {save_certificates}")
    
    # Validate and set DNS plugin
    if hosting_provider not in DNS_PLUGIN_MAP:
        raise ValueError(f"Unsupported hosting provider: {hosting_provider}")
    dns_plugin = DNS_PLUGIN_MAP[hosting_provider]
    #os.system(f"pip install certbot-{dns_plugin}")

def get_provider_instances(
    config: Dict[str, Any],
    included_providers: Optional[List[str]] = None,
    excluded_providers: Optional[List[str]] = None
) -> Dict[str, Any]:

    # Filter and return provider instances based on inclusion/exclusion lists.
    included_providers = included_providers or []
    excluded_providers = excluded_providers or []
    
    filtered_providers: Dict[str, Any] = {}

    for provider, instances in config["providers"].items():
        # Skip if provider is not in included list (when included list is not empty)
        if included_providers and provider not in included_providers:
            logger.debug(f"{provider} was skipped (not in included providers)")
            continue
            
        # Skip if provider is in excluded list
        if provider in excluded_providers:
            logger.debug(f"{provider} was skipped (in excluded providers)")
            continue
            
        filtered_providers[provider] = instances
        
    return filtered_providers

def get_certificate_manager_class(provider: str) -> str:

    # Get the certificate manager class name for a provider.
    if provider not in CERTIFICATE_MANAGER_MAP:
        raise ValueError(f"Provider {provider} not supported")
    
    return CERTIFICATE_MANAGER_MAP[provider]

def get_instance_config(instance: Dict[str, str], required_parameters: List[str]) -> Dict[str, str]:

    # Extract and resolve environment variables for an instance configuration.
    # Extract environment variable names from the instance config
    env_var_names = {
        key: instance.get(f"{key}_env_var")
        for key in required_parameters
    }
    
    # Resolve environment variables to their actual values and strip quotes
    instance_config = {
        key: os.getenv(env_var_name)
        for key, env_var_name in env_var_names.items()
        if env_var_name is not None
    }
    # To resolve a possible quote issue use this instead:
    # instance_config = {
    #     key: os.getenv(env_var_name).strip('"\'') if os.getenv(env_var_name) is not None else None
    #     for key, env_var_name in env_var_names.items()
    #     if env_var_name is not None
    # }
    
    # Check for missing parameters
    missing_params = [key for key in required_parameters if key not in instance_config]
    if missing_params:
        raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
        
    return instance_config 