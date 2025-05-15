# Standard library imports
import requests
import logging
import logging.config
import xml.etree.ElementTree as ET

# Third party imports
import requests

# Local imports
from certbot_utils import *
from certificatemanager_abc import CertificateManager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("paloalto")

### Creating the PaloAltoCertificateManager object for managing the renewal of the SSL certificate ###

class PaloAltoCertificateManager(CertificateManager):
    @staticmethod
    def get_required_parameters():
        return ["domain", "api_token", "passphrase"]

    def __init__(self, domain, api_token, passphrase):
        self.domain = domain
        self.api_token = api_token
        self.passphrase = passphrase

        #self.username = username
        #self.password = passowrd

        self.url_api = f"https://{self.domain}/api"
        logger.debug(f"API url: {self.url_api}")

    # Can be used if you need to generate a new API key. You have to do this step manually
    def generate_new_api_key(self):
        #response = requests.post(url=self.url_get, headers=self.headers_get, verify=False)
        params = {
            "type":"keygen",
            "user": self.username,
            "password": self.password
        }
        response_api_key = requests.get(url=self.url_api, params=params, verify=False)
        logger.debug(f"API key response status code: {response_api_key.status_code}")
        logger.debug(f"API key response text: {response_api_key.text}")

    ### Logic how to renew a certificate for PaloAlto instances ###

    def execute_test(self):
        logger.info(f"PaloAlto instance parameters: Domain: {self.domain} and API_Token: {self.api_token} is provided.")

    def execute_certificate_renewal(self):

        try:
            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(domain=self.domain, key_type="rsa")

            try:
                # The following two commands encrypt the private key with AES256 and set a password for it with the given passphrase
                os.system(f"openssl rsa -aes256 -in /etc/letsencrypt/live/{self.domain}/privkey.pem -out /etc/letsencrypt/live/{self.domain}/privkeynew.pem -passout pass:{self.passphrase}")
                os.system(f"mv /etc/letsencrypt/live/{self.domain}/privkeynew.pem /etc/letsencrypt/live/{self.domain}/privkey.pem")
            
            except ValueError:
                logger.error(f"Couldnt encrypt the private key.")
                raise
    
            # Get the required paths
            key_path, fullChain_path, paloalto_path = certificate_paths(domain=self.domain, requested_paths=["key_path", "fullChain_path", "paloalto_path"])
    
            concat_certificates_paloalto(key_path=key_path, fullChain_path=fullChain_path, paloalto_path=paloalto_path)
    
            # Load all files to open their content
            loaded_files = load_certificate_files("binary", paloalto_path=paloalto_path)
            paloalto_file = loaded_files.get("paloalto_path")
    
            new_certificate_name = generate_certificate_name(domain=self.domain)
    
            # Post the newly generated certificate
            self.post_new_certificate(paloalto_file=paloalto_file, new_certificate_name=new_certificate_name)

            # Replace the old with the new certificate
            self.exchange_new_certificate(new_certificate_name)

            # Get the name of the old certificate to later be able to delete it
            old_certificate_name = self.get_old_certificate_name(new_certificate_name)
    
            # Delete the old certificate
            self.delete_certificate(old_certificate_name)

            # Commit all the changes
            self.commit_certificate()

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise        

    ### Different tasks are handled by the below functions that are needed for the execute function ###

    def get_certificate_information(self):
        params = {
            "key": self.api_token,
            "type": "config",
            "action": "get",
            "xpath": "/config/shared/certificate"
        }

        get_certificate_information_response = requests.get(url=self.url_api, params=params)

        if get_certificate_information_response.status_code != 200:
            logger.error(f"Couldn't not retrieve certificate information. API response:\n{get_certificate_information_response.text}")
            raise
        
        logger.debug(f"Get certificate information was successful")

        return get_certificate_information_response
        
    def post_new_certificate(self, paloalto_file, new_certificate_name):
        files = {
            "file": paloalto_file
        }

        params = {
            "key": self.api_token,
            "type": "import",
            "category": "keypair",
            "certificate-name": new_certificate_name,
            "format": "pem",
            "passphrase": self.passphrase
        }

        post_certificate_response = requests.post(url=self.url_api, params=params, files=files)

        if ET.fromstring(post_certificate_response.text).attrib.get("status") != "success":
            logger.error(f"Couldn't post the new certificate. API response:\n {post_certificate_response.text}")
            raise

        logger.debug("Successfully posted the new certificate")
    
    def exchange_new_certificate(self, new_certificate_name):
        # The value of the @name= needs to fit to the profile you have on your Paloalto firewall
        params = {
            "key": self.api_token,
            "type": "config",
            "action": "set",
            "xpath": f"/config/shared/ssl-tls-service-profile/entry[@name='letsencrypt']",
            "element": f"<certificate>{new_certificate_name}</certificate>"
        }

        exchange_certificate_response = requests.post(url=self.url_api, params=params, verify=False)

        if ET.fromstring(exchange_certificate_response.text).attrib.get("status") != "success":
            logger.error(f"Couldn't exchange the new with the old certificate. API response:\n {exchange_certificate_response.text}")
            raise

        logger.debug("Successfully exchanged the new with the old certificate")

    def get_old_certificate_name(self, new_certificate_name):
        # Get a certificate overview via API
        get_certificate_information_response = self.get_certificate_information()

        # Convert it with the ET library to XML code to later filter for the tags
        root = ET.fromstring(get_certificate_information_response.text)

        try:
            # Create a list
            certificate_names = []

            # Extract the names from the 'name' attributes of the <entry> tags
            for entry in root.findall(".//entry"):
                name = entry.get("name")
                if name:
                    certificate_names.append(name)
        
        except:
            logger.error(f"Wasn't able to extract names from the API response:\n{root}")
            raise
    
        try:
            # Loop through certificate names list and filter out the one which is not the newly created but has the same domain as a name
            old_certificate_name = next ((name for name in certificate_names if name.startswith(self.domain) and name != new_certificate_name), None)

            if old_certificate_name is None:
                logger.error(f"Old certificate name can't be 'None'. Certificate names: {certificate_names}")
                raise

            return old_certificate_name

        except:
            logger.error(f"Couldn't filter the name out of the certificate names list:\n{certificate_names}")
            raise
    
    def delete_certificate(self, old_certificate_name):
        params = {
            "key": self.api_token,
            "type": "config",
            "action": "delete",
            "xpath": f"/config/shared/certificate/entry[@name='{old_certificate_name}']"
        }

        delete_certificate_response = requests.post(url=self.url_api, params=params, verify=False)

        if ET.fromstring(delete_certificate_response.text).attrib.get("status") != "success":
            logger.error(f"Couldn't delete the old certificate. API response:\n{delete_certificate_response.text}")
            raise
        
        logger.debug("Successfully deleted the old certificate")

    def commit_certificate(self):
        params = {
            "key": self.api_token,
            "type": "commit",
            "cmd": "<commit></commit>"
        }

        commit_response = requests.get(url=self.url_api, params=params, verify=False)

        if ET.fromstring(commit_response.text).attrib.get("status") != "success":
            logger.error(f"Couldn't delete the old certificate. API response:\n {commit_response.text}")
            raise

        logger.debug("All changes were successfully commited")
