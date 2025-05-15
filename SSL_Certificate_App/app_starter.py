# Standard library imports

import logging
import logging.config
import os
from pathlib import Path

# Local imports
from renew_system_certificates import renew_provider_certificates

# Load logging configuration

logging.config.fileConfig("logging.ini")
logger = logging.getLogger("app_starter")

# Starting the script -> three required variables that can be modified if needed
# include_provider -> if you only want to test sample size of all providers
# exclude_provider -> if you want to test nearly all providers except specific ones
# config_file_path -> path to your "config.json" file

def main():
    logger.info("Starting the application")
    
    try:
        
        # Set included and excluded providers
        included_providers = None  # Set to None to include all providers
        excluded_providers = None  # Set to None to exclude none
        
        logger.debug(f"Included providers: {included_providers}")
        logger.debug(f"Excluded providers: {excluded_providers}")
        
        # Start certificate renewal process
        renew_provider_certificates(
            included_providers=included_providers,
            excluded_providers=excluded_providers,
            config_file_path="config.json"
        )
        
    except Exception as e:
        logger.critical(f"Application failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
