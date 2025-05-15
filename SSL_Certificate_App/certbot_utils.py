# Standard library imports
import os
import logging
import logging.config
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

# Local imports
import config_manager as config_manager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("certbot_utils")

# Global set to track domains that need certificates saved
domains_to_save = set()

def create_instance_certificate(domain, key_type):
    logger.debug(f"Key type for certificate generation is: {key_type}")
    logger.debug(f"Notification email for certificate generation is: {config_manager.notification_email}")
    logger.debug(f"DNS plugin for certificate generation is: {config_manager.dns_plugin}")

    # Executing a shell command using the certbot library for generating the Let's Encrypt SSL certificate for a specific domain. 
    # Include the --test-cert flag if you want to test certificate generation.
    try:
        os.system(f"certbot certonly --config-dir {config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt --work-dir {config_manager.DEFAULT_CERTIFICATE_FOLDER}/var/lib/letsencrypt --logs-dir {config_manager.DEFAULT_CERTIFICATE_FOLDER}/var/log/letsencrypt --{config_manager.dns_plugin} -d {domain} -n --agree-tos --key-type {key_type} -m {config_manager.notification_email}")

        if os.path.exists(f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}"):
            logger.info(f"Certificate for {domain} was issued successfully")
            
            # Add domain to list of domains to save
            save_certificates_to_zip(domain)
        else:
            logger.error(f"Certificate for {domain} was not issued successfully")
            raise
    except ValueError:
        logger.error("Your inputs for the 'certbot' command aren't valid. Please check if you own the domain and if you entered a valid key type.")
        raise
    except Exception as e:
        logger.error(f"An error occurred while generating the certificate for {domain}: {str(e)}")
        raise

    logger.info(f"Certificate for {domain} was issued successfully")

def certificate_paths(domain: str, requested_paths: list[str]) -> tuple[str, ...]:

    logger.debug(f"Required paths that are getting requested: {requested_paths}")

    # All paths that are needed for finding a file are entered here
    PATH_MAP = {
        "fullChain_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/fullchain.pem",
        "caChain_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/chain.pem",
        "cert_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/cert.pem",
        "key_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/privkey.pem",
        "vsphereSSL_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/vsphere.pem",
        "hycu_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/hycu.pem",
        "vamax_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/vamax.pem",
        "paloalto_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/paloalto.pem",
        "rootChain_path": f"{config_manager.DEFAULT_CERTIFICATE_FOLDER}/etc/letsencrypt/live/{domain}/root.pem"
    }

    return tuple(PATH_MAP[path] for path in requested_paths if path in PATH_MAP)

def generate_certificate_name(domain):

    # Certificate name is generated using the domain and the current time (including seconds) for having a unique file name.
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    certificate_name = f"{domain}_{timestamp}"
    logger.debug(f"The generated certificate name is: {certificate_name}")

    return certificate_name

def load_certificate_files(read_mode, **file_paths):
    logger.debug(f"Readmode for the files is: {read_mode}. And the file paths are: {file_paths}.")

    loaded_files = {}

    for file_name, file_path in file_paths.items():
        try:
            # The 'binary' readmode is needed if no decoding is required and your data is getting red as bytes
            if read_mode == "binary":
                loaded_files[file_name] = Path(file_path).read_bytes()

            # The 'text' readmode is need if the files should be decoded (default is utf-8) and your data is getting treated as a string.
            elif read_mode == "text":
                loaded_files[file_name] = Path(file_path).read_text()

            else:
                logger.error(f"Unsupported read_mode {read_mode}. Use 'binary' or 'text'.")
                raise

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

    logger.debug("Files were loaded successfully")

    return loaded_files

def get_output_directory() -> Path:
    
    # Get the output directory for certificates from environment variable or use default.
    # The CERTIFICATE_OUTPUT_DIR environment variable should point to a mounted volume.
    output_dir = os.getenv('CERTIFICATE_OUTPUT_DIR')
    if not output_dir:
        logger.warning("CERTIFICATE_OUTPUT_DIR not set, using default 'certificates' directory")
        output_dir = config_manager.DEFAULT_CERTIFICATE_FOLDER
    return Path(output_dir)

def save_certificates_to_zip(domain: str) -> None:

    # Add a domain to the list of domains whose certificates need to be saved.
    # The actual saving will happen when create_final_certificate_zip is called.
    if config_manager.save_certificates != "y":
        logger.debug("Certificate saving is disabled")
        return

    domains_to_save.add(domain)
    logger.debug(f"Added {domain} to domains to save")

def create_final_certificate_zip() -> str:

    # Create a single zip file containing all certificates for all domains.
    # Returns the path to the zip file if created, None otherwise.
    if not domains_to_save or config_manager.save_certificates != "y":
        logger.debug("No certificates to save")
        return None

    try:
        # Get output directory from environment variable
        output_dir = get_output_directory()

        # Create a temporary directory for all certificates
        temp_dir = Path("/tmp/certificates_temp")
        temp_dir.mkdir(exist_ok=True)

        # Process each domain
        for domain in domains_to_save:
            # Create domain-specific directory
            domain_dir = temp_dir / domain
            domain_dir.mkdir(exist_ok=True)

            # Get all certificate paths for this domain
            cert_paths = certificate_paths(domain, [
                "fullChain_path", "caChain_path", "cert_path", "key_path",
                "vsphereSSL_path", "hycu_path", "vamax_path", "paloalto_path",
                "rootChain_path"
            ])

            # Copy all certificate files to the domain directory
            for cert_path in cert_paths:
                if os.path.exists(cert_path):
                    file_name = os.path.basename(cert_path)
                    shutil.copy2(cert_path, domain_dir / file_name)

        # Create zip file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = output_dir / f"all_certificates_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for domain_dir in temp_dir.glob('*'):
                if domain_dir.is_dir():
                    for file_path in domain_dir.glob('*'):
                        # Store files in zip with domain name as prefix
                        zipf.write(file_path, f"{domain_dir.name}/{file_path.name}")

        # Clean up temporary directory
        shutil.rmtree(temp_dir)

        logger.info(f"All certificates saved to {zip_path}")
        return str(zip_path)

    except Exception as e:
        logger.error(f"Failed to create final certificate zip: {str(e)}")
        return None

### All concatenation functions to generate a specific file based on the provider if the provider needs the files provided by Let's Encrypt in a given order. ###

def concat_certificates_vsphere(cert_path, caChain_path, rootChain_path, vsphereSSL_path):
    try:
        os.system(f"cat {cert_path} {caChain_path} isrgrootx1.pem > {vsphereSSL_path}")
        logger.debug(f"File was concatenated to {vsphereSSL_path}")
        os.system(f"cat {caChain_path} isrgrootx1.pem > {rootChain_path}")
        logger.debug(f"File was concatenated to {rootChain_path}")
    
    except ValueError:
        logger.error(f"Can't concatenate the files to your specified location. The provided paths were:\n{cert_path},\n{caChain_path},\n{rootChain_path},\n{vsphereSSL_path}")
        raise

def concat_certificates_vamax(key_path, cert_path, caChain_path, vamax_path):
    try:
        os.system(f"cat {key_path} {cert_path} {caChain_path} isrgrootx1.pem > {vamax_path}")
        logger.debug(f"File was concatenated to {vamax_path}")

    except ValueError:
        logger.error(f"Can't concatenate the files to your specified location. The provided paths were:\n{key_path},\n{cert_path},\n{caChain_path},\n{vamax_path}")
        raise

def concat_certificates_hycu(cert_path, caChain_path, hycu_path):
    try:
        os.system(f"cat {cert_path} {caChain_path} isrgrootx1.pem > {hycu_path}")
        logger.debug(f"File was concatenated to {hycu_path}")

    except ValueError:
        logger.error(f"Can't concatenate the files to your specified location. The provided paths were:\n{cert_path},\n{caChain_path},\n{hycu_path}")
        raise

def concat_certificates_paloalto(key_path, fullChain_path, paloalto_path):
    try:
        os.system(f"cat {key_path} {fullChain_path} > {paloalto_path}")
        logger.debug(f"File was concatenated to {paloalto_path}")

    except ValueError:
        logger.error(f"Can't concatenate the files to your specified location. The provided paths were:\n{key_path},\n{fullChain_path},\n{paloalto_path}")
        raise


