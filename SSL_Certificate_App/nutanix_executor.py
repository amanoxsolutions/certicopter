# Standard library imports
import base64
import json
import logging
import logging.config
from datetime import datetime

# Third party imports
import requests

# Local imports
from certificatemanager_abc import CertificateManager
from certbot_utils import *

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("nutanix")

### Creating the NutanixCertificateManager object for managing the renewal of the SSL certificate ###

class NutanixCertificateManager(CertificateManager):

    # Static method to return what the provider specific requirements are regarding needed parameters for the certificate renewal process
    @staticmethod
    def get_required_parameters():
        return ["domain", "username", "password"]
    
    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password
        self.auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.secure_url = f"https://{self.domain}:9440"
        logger.debug(f"Connection url: {self.secure_url}")
        self.url_get = f"{self.secure_url}/PrismGateway/services/rest/v1/keys/pem"
        logger.debug(f"Get url: {self.url_get}")
        self.url_post = f"{self.secure_url}/PrismGateway/services/rest/v1/keys/pem/import"
        logger.debug(f"Post url: {self.url_post}")
        
        self.headers_get = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth}",
        }
        self.headers_post = {
            "Accept": "application/json",
            "Content-Type": "multipart/form-data",
            "Authorization": f"Basic {self.auth}",
        }

    ### Logic how to renew a certificate for Nutanix instances ###
    def execute_test(self):
        logger.info(f"Nutanix instance parameters: Domain {self.domain}, Username {self.username} and password {self.password} is provided.")

    def execute_certificate_renewal(self):

        try:
            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(domain=self.domain, key_type="rsa")

            # Open necessary files
            key_path, cert_path, caChain_path  = certificate_paths(domain=self.domain, requested_paths=["key_path", "cert_path", "caChain_path"])
            loaded_files = load_certificate_files(read_mode="binary", key_path=key_path, cert_path=cert_path, caChain_path=caChain_path)
            
            key_file = loaded_files.get("key_path")
            cert_file = loaded_files.get("cert_path")
            caChain_file = loaded_files.get("caChain_path")

            # Post the new certificate with the opened files
            self.post_new_certificate(key_file=key_file, cert_file=cert_file, caChain_file=caChain_file)

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise
    
    ### Different tasks are handled by the below functions that are needed for the execute function ###

    def post_new_certificate(self, key_file, cert_file, caChain_file):
        files = {
            'keyType': 'RSA_2048',
            'key': key_file,
            'cert': cert_file,
            'caChain': caChain_file
        }

        post_certificate_response = requests.post(url=self.url_post, files=files, headers=self.headers_post, verify=False)

        if post_certificate_response.status_code != 200:
            logger.error(f"Couldn't post the certificate to {self.domain}. API response:\n{post_certificate_response}")
            raise
        
        logger.debug(f"Posting new certificate was successful")

    
    ### Not used for renewal process but can be helpful for debugging ###

    def get_certificate_information(self):
        certificate_information_response = requests.get(url=self.url_get, headers=self.headers_get, verify=False)
    
        return json.loads(certificate_information_response.text)
