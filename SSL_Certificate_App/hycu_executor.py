# Standard library imports
import json
import logging
import logging.config
from operator import itemgetter

# Third party imports
import requests

# Local imports
from certbot_utils import *
from certificatemanager_abc import CertificateManager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("hycu")

### Creating the HYCUCertificateManager object for managing the renewal of the SSL certificate ###

class HYCUCertificateManager(CertificateManager):

     # Static method to return what the provider specific requirements are regarding needed parameters for the certificate renewal process
    @staticmethod
    def get_required_parameters():
        return ["domain", "dns_ip_addresses", "api_token"]
    
    def __init__(self, domain, dns_ip_addresses, api_token):
        self.domain = domain
        self.dns_ip_addresses = str(dns_ip_addresses)
        self.api_token = api_token
        self.secure_url = f"https://{self.domain}:8443"
        logger.debug(f"Connection url: {self.secure_url}")
        self.url_certificate = f"{self.secure_url}/rest/v1.0/certificate"
        logger.debug(f"Post url: {self.url_certificate}")
        self.url_network = f"{self.secure_url}/rest/v1.0/networks"
        logger.debug(f"Change certificate url: {self.url_network}")

        self.headers_api = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    ### Logic how to renew a certificate for HYCU instances ###

    def execute_test(self):
        logger.info(f"HYCU instance parameters: Domain: {self.domain}, IPs: {self.dns_ip_addresses} and API_Token: {self.api_token} is provided.")

    def execute_certificate_renewal(self):

        try:

            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(domain=self.domain, key_type="ecdsa")

            # Open necessary files
            key_path, cert_path, caChain_path, hycu_path  = certificate_paths(domain=self.domain, requested_paths=["key_path", "cert_path", "caChain_path", "hycu_path"])
            
            # Concatenate the different certificates to match the requirements of HYCU
            concat_certificates_hycu(cert_path=cert_path, caChain_path=caChain_path, hycu_path=hycu_path)

            # Load all files to open their content
            loaded_files = load_certificate_files(read_mode="text", key_path=key_path, hycu_path=hycu_path)
            key_file = loaded_files.get("key_path")
            hycu_file = loaded_files.get("hycu_path")
            
            # Generate a certificate name
            certificate_name = generate_certificate_name(domain=self.domain)
            
            # Post the new certificate
            self.post_new_certificate(certificate_name=certificate_name, key_file=key_file, hycu_file=hycu_file)

            # Extract the UUID of the old certificate
            extracted_uuid = self.extract_uuid()

            # Get old and new certificate informations
            information_about_certificates = self.get_certificate_information()
            old_certificate_id, new_certificate_id = self.get_old_and_new_certificate_id(information_about_certificates)

            # Exchange the old with the new SSL certificate and delete the old one after a successful exchange
            self.exchange_new_with_old_certificate(new_certificate_id=new_certificate_id, extracted_uuid=extracted_uuid)

            # Delete the old certificate
            self.delete_old_certificate(old_certificate_id)

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise

    ### Different tasks are handled by the below functions that are needed for the execute function ###

    def post_new_certificate(self, certificate_name, key_file, hycu_file):
        payload = {
            "name":f"{certificate_name}",
            "privateKey": key_file,
            "certificate": hycu_file
        }

        post_certificate_response = requests.post(url=self.url_certificate, json=payload, headers=self.headers_api, verify=False)

        if post_certificate_response.status_code != 201:
            logger.error(f"Couldn't post the certificate to {self.domain}. API response:\n{post_certificate_response}")
            raise

        logger.debug(f"Posting certificate was successful")

    def extract_uuid(self):
        network_overview_response = requests.get(url=self.url_network, headers=self.headers_api, verify=False)

        if network_overview_response.status_code != 200:
            logger.error(f"Couldn't get network overview:\n{network_overview_response}")
            raise

        network_entity = json.loads(network_overview_response.text)

        try:
            if network_entity.get("entities"):
                extracted_uuid = network_entity["entities"][0].get("uuid")
                logger.debug(f"The old UUID is: {extracted_uuid}")

                return extracted_uuid
            
        except KeyError:
            logger.error(f"There was a problem with extracting the UUID")
            raise

    def get_certificate_information(self):
        information_about_certificates = requests.get(url=self.url_certificate, headers=self.headers_api, verify=False)

        if information_about_certificates.status_code != 200:
            logger.error(f"Couldn't get network overview:\n{information_about_certificates}")
            raise
        
        logger.debug("Information about certificates could be retrieved")

        return json.loads(information_about_certificates.text)
    
    def get_old_and_new_certificate_id(self, information_about_certificates):
         
         try:
            entities = information_about_certificates['entities']

         except KeyError:
            logger.error("The tag 'entities' doesn't exist in the API response")
            raise

         filtered_entities = [entity for entity in entities if entity['name'].startswith(f"{self.domain}")]

         if len(filtered_entities) > 1:
             
            try:
                earliest_entity = min(filtered_entities, key=itemgetter("expires"))
                earliest_uuid = earliest_entity['uuid']
                newest_entity = max(filtered_entities, key=itemgetter("expires"))
                newest_uuid = newest_entity['uuid']

                logger.debug(f"Old certificate UUID ({earliest_uuid}) and new certificate UUID ({newest_uuid}) gathered")

                return earliest_uuid, newest_uuid
            
            except KeyError as e:
                logger.error(f"Weren't able to retrieve values for the UUIDs:\n{e}")
         
         else:
             logger.error("There isn't more then one certificate. Comparison between new and old certificate can't be done.")
             raise
    
    def exchange_new_with_old_certificate(self, new_certificate_id, extracted_uuid):
        payload = {
            "dns": self.dns_ip_addresses,
            "certificateUuid": new_certificate_id
        }

        exchange_url = f"{self.url_network}/{extracted_uuid}"
        logger.debug(f"Exchange url: {exchange_url}")

        exchange_certificate_response = requests.patch(url=exchange_url, json=payload, headers=self.headers_api, verify=False)

        if exchange_certificate_response.status_code != 202:
            logger.error(f"Couldn't get exchange certificate:\n{exchange_certificate_response}")
            raise

        logger.debug("Exchange of certificate was successful")
    
    def delete_old_certificate(self, old_certificate_id):
        deletion_url = f"{self.url_certificate}/{old_certificate_id}"
        logger.debug(f"Deletion url is: {deletion_url}")

        delete_certificate_response = requests.delete(url=deletion_url, headers=self.headers_api, verify=False)

        if delete_certificate_response.status_code != 200:
            logger.error(f"Couldn't delete the old certificate:\n{delete_certificate_response}")
            raise

        logger.debug("Deletion of the old certificate was successful")

