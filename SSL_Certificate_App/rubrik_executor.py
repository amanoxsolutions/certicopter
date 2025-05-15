# Standard library imports
import logging
import logging.config

# Third party imports
import requests

# Local imports
from certbot_utils import *
from certificatemanager_abc import CertificateManager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("rubrik")

### Creating the RubrikCertificateManager object for managing the renewal of the SSL certificate ###

class RubrikCertificateManager(CertificateManager):
    
     # Static method to return what the provider specific requirements are regarding needed parameters for the certificate renewal process
    @staticmethod
    def get_required_parameters():
        return ["domain", "api_token"]

    def __init__(self, *, domain, api_token):
        self.domain = domain
        self.api_token = api_token
        self.secure_url = f"https://{self.domain}"
        logger.debug(f"Connection url: {self.secure_url}")
        self.url_certificate = f"{self.secure_url}/api/v1/certificate"
        logger.debug(f"Post url: {self.url_certificate}")
        self.url_cluster_settings =f"{self.secure_url}/api/v1/cluster/me/security/web_signed_cert"
        logger.debug(f"Change settings url: {self.url_cluster_settings}")

        self.headers_api = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    ### Logic how to renew a certificate for Rubrik instances ###

    def execute_test(self):
        logger.info(f"Rubrik instance parameters: Domain: {self.domain} and API_Token: {self.api_token} is provided.")

    def execute_certificate_renewal(self):

        try:
            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(domain=self.domain, key_type="rsa")
            
            # Open necessary files
            key_path, fullChain_path = certificate_paths(domain=self.domain, requested_paths=["key_path", "fullChain_path"])
            loaded_files = load_certificate_files("text", key_path=key_path, fullChain_path=fullChain_path)

            key_file = loaded_files.get("key_path")
            fullChain_file = loaded_files.get("fullChain_path")

            # Get the old certificate ID
            old_certificate_id = self.get_old_certificate_id()
            logger.debug(f"Old certificate ID: {old_certificate_id}")

            # Generate a certificate name
            certificate_name = generate_certificate_name(domain=self.domain)

            # Post the new certificate
            self.post_new_certificate(certificate_name=certificate_name, key_file=key_file, fullChain_file=fullChain_file)

            # Get the new certificate ID
            new_certificate_id = self.compare_certificate_ids(old_certificate_id)
            logger.debug(f"New certificate ID: {new_certificate_id}")

            # Change the cluster settings to exchange the old with the new certificate
            self.change_cluster_certificate_settings(new_certificate_id)

            # Delete the old certificate
            self.delete_old_certificate(old_certificate_id)

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise

    ### Different tasks are handled by the below functions that are needed for the execute function ###

    def get_old_certificate_id(self):
        get_certificate_response = requests.get(url=self.url_certificate, headers=self.headers_api, verify=False)
        if get_certificate_response.status_code != 200:
            logger.error(f"Couldn't retrieve certificate information:\n{get_certificate_response.text}")
            raise
        
        try:
            for field in get_certificate_response.json()["data"]:
                old_certificate_id = field["certId"]

        except KeyError:
            logger.error(f"Old certificate ID couldn't be retrieved:\n{get_certificate_response.text}")
            raise

        logger.debug(f"Old certificate ID: {old_certificate_id}")

        return old_certificate_id
        
    def post_new_certificate(self, certificate_name, key_file, fullChain_file):
        payload = {
            "hasKey": "true",
            "name": f"{certificate_name}",
            "pemFile": fullChain_file,
            "privateKey": key_file
        }

        post_certificate_response = requests.post(url=self.url_certificate, headers=self.headers_api, json=payload, verify=False)

        if post_certificate_response.status_code != 200:
            logger.error(f"Couldn't post the certificate to {self.domain}. API response:\n{post_certificate_response.text}")
            raise
        
        logger.debug(f"Posting certificate was successful")
    
    def compare_certificate_ids(self, old_certificate_id):   
        get_certificate_response = requests.get(url=self.url_certificate, headers=self.headers_api, verify=False)
        
        if get_certificate_response.status_code != 200:
            logger.error(f"Couldn't retrieve certificate informations:\n{get_certificate_response.text}")
            raise

        try:
            for field in get_certificate_response.json()["data"]:
                certificate_id_holder = field["certId"]
            
                if certificate_id_holder != old_certificate_id:
                    new_certificate_id = field["certId"]
                    logger.debug(f"New certificate ID is: {new_certificate_id}")
                    return new_certificate_id
                
        except KeyError:
            logger.error(f"New certificate ID couldn't be retrieved:\n{get_certificate_response.text}")
            raise

    
    def change_cluster_certificate_settings(self, new_certificate_id):
        payload = {
            "certificateId": new_certificate_id
        }

        # Maybe needs to be done two times because of a bug with Rubrik (if you get an error here could be because of this)
        change_cluster_settings_response = requests.put(url=self.url_cluster_settings, headers=self.headers_api, json=payload, verify=False)

        if change_cluster_settings_response.status_code != 202:
            logger.error(f"Couldn't change cluster settings:\n{change_cluster_settings_response.text}")
            raise

        logger.debug(f"Change old with new certificate was successful")

    def delete_old_certificate(self, old_certificate_id):
        url_delete = f"{self.url_certificate}/{old_certificate_id}"
        logger.debug(f"Delete url: {url_delete}")

        delete_certificate_response = requests.delete(url=url_delete, headers=self.headers_api, verify=False)

        if delete_certificate_response.status_code != 204:
            logger.error(f"Couldn't delete the old certificate:\n{delete_certificate_response.text}")
            raise

        logger.debug(f"Deleting old certificate was successful")



    
