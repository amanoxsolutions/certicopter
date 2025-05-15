# Standard library imports
import base64
import logging
import logging.config

# Third party imports
import requests

# Local imports
from certbot_utils import *
from certificatemanager_abc import CertificateManager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("vsphere")

### Creating the VSphereCertificateManager object for managing the renewal of the SSL certificate ###

class VSphereCertificateManager(CertificateManager):

     # Static method to return what the provider specific requirements are regarding needed parameters for the certificate renewal process
    @staticmethod
    def get_required_parameters():
        return ["domain", "username", "password"]

    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password
        self.auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        self.secure_url = f"https://{self.domain}"
        logger.debug(f"Connection url: {self.secure_url}")
        self.session_url = f"{self.secure_url}/api/session"
        logger.debug(f"Session ID url: {self.session_url}")
        self.post_url = (f"{self.secure_url}/api/vcenter/certificate-management/vcenter/tls")
        logger.debug(f"Post url: {self.post_url}")

        self.headers_get = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth}",
        }

    ### Logic how to renew a certificate for VSphere instances ###
    def execute_test(self):
        logger.info(f"VSphere instance parameters: Domain: {self.domain}, User: {self.username} and Password: {self.password} is provided.")

    def execute_certificate_renewal(self):

        try:
            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(self.domain, key_type="rsa")

            # Get the required paths
            key_path, cert_path, caChain_path, rootChain_path, vsphereSSL_path = certificate_paths(domain=self.domain, requested_paths=["key_path", "cert_path", "caChain_path", "rootChain_path", "vsphereSSL_path"])

            # Concatenate the different certificates to match the requirements of VSphere
            concat_certificates_vsphere(cert_path=cert_path, caChain_path=caChain_path, rootChain_path=rootChain_path, vsphereSSL_path=vsphereSSL_path)

            # Load all files to open their content
            loaded_files = load_certificate_files(read_mode="text", key_path=key_path, rootChain_path=rootChain_path, vsphereSSL_path=vsphereSSL_path)
            key_file = loaded_files.get("key_path")
            root_file = loaded_files.get("rootChain_path")
            vsphereSSL_file = loaded_files.get("vsphereSSL_path")

            # Get the current session ID of the VSphere instance
            session_id = self.get_vmware_session_id()

            # Post the new certificate
            self.post_new_certificate(session_id=session_id, key_file=key_file, root_file=root_file, vsphereSSL_file=vsphereSSL_file)

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise

    ### Different tasks are handled by the below functions that are needed for the execute function ###
    
    def get_vmware_session_id(self):
        try:
            get_session_id_response = requests.post(url=self.session_url, headers=self.headers_get, verify=False)

            if get_session_id_response.status_code == 201:
                # Strip any leading or trailing single ('') or double ("") quotes from the session ID
                session_id = get_session_id_response.text.strip('\'"')
                logger.debug(f"Session ID is: {session_id}")

                return session_id

        except:
            logger.error(f"Failed to create a session ID: {get_session_id_response.text}")
            raise

    def post_new_certificate(self, session_id, key_file, root_file, vsphereSSL_file):
        headers_post = {
            "vmware-api-session-id": session_id
        }

        files = {
            "cert": vsphereSSL_file,
            "key": key_file,
            "root_cert": root_file,
        }

        post_certificate_response = requests.put(url=self.post_url, json=files, headers=headers_post, verify=False)

        if post_certificate_response.status_code != 204:
            logger.error(f"Couldn't post the certificate to {self.domain}. API response:\n{post_certificate_response.text}")
            raise            

        logger.debug(f"Posting new certificate was successful")
