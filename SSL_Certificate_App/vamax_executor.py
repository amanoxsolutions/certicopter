# Standard library imports
import re
import logging
import logging.config
from datetime import datetime

# Third party imports
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

# Local imports
from certbot_utils import *
from certificatemanager_abc import CertificateManager

# Load logging configuration
logging.config.fileConfig("logging.ini")
logger = logging.getLogger("vamax")

### Creating the VAMaxCertificateManager object for managing the renewal of the SSL certificate ###

class VAMaxCertificateManager(CertificateManager):

    # Static method to return what the provider specific requirements are regarding needed parameters for the certificate renewal process
    @staticmethod
    def get_required_parameters():
        return ["domain", "username", "password"]

    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password
        self.secure_url = f"https://{self.domain}:9443"
        logger.debug(f"Connection url: {self.secure_url}")
        self.url_get = f"{self.secure_url}/lbadmin/ajax/get_ssl.php"
        logger.debug(f"Get url: {self.url_get}")
        self.url_ssl_category = f"{self.secure_url}/lbadmin/config/sslcert.php"
        logger.debug(f"Post url: {self.url_ssl_category}")
        self.url_security_category = f"{self.secure_url}/lbadmin/config/secure.php"
        logger.debug(f"Change settings url: {self.url_security_category}")

        # If you want to use the VAMax API then initialize the following variables
        #self.api_token = os.environ.get(api_token_env_var)
        #self.api_token_encoded = b64encode(self.api_token.encode())
        #self.data = '{"lbcli":[{"action":"termination","function":"list", "type":"certificate"}]}'
        #self.url_api = f"{self.secure_url}/api/v2/"
        #self.headers_get = {
        #    "X-LB-APIKEY": self.api_token_encoded,
        #    "Content-Type": "application/json"
        #}
        #self.headers_post = {
        #    "X-LB-APIKEY": self.api_token_encoded,
        #    "Content-Type": "multipart/form-data"
        #}

    ### Logic how to renew a certificate for Nutanix instances ###
    def execute_test(self):
        logger.info(f"VAMax instance parameters: Domain: {self.domain}, User: {self.username} and Password: {self.password} is provided.")

    def execute_certificate_renewal(self):

        try:            
            # Get the SSL certificate from Let's Encrypt with Certbot
            create_instance_certificate(domain=self.domain, key_type="ecdsa")

            # Get the required paths
            key_path, cert_path, caChain_path, vamax_path = certificate_paths(domain=self.domain, requested_paths=["key_path", "cert_path", "caChain_path", "vamax_path"])

            # Concatenate the different certificates to match the requirements of VAMax
            concat_certificates_vamax(key_path=key_path, cert_path=cert_path, caChain_path=caChain_path, vamax_path=vamax_path)

            # Load all files to open their content
            loaded_files = load_certificate_files(read_mode="binary", vamax_path=vamax_path)
            vamax_file = loaded_files.get("vamax_path")

            # Generate a certificate name
            new_certificate_name = generate_certificate_name(domain=self.domain)

            ## Get certificate information if needed
            ##cert_info = self.get_certificate_information()
            ##logger.debug(f"Certificate information: {cert_info}")

            # Post the new certificate
            self.post_new_certificate(vamax_file=vamax_file, new_certificate_name=new_certificate_name)

            # Exchange the old with the new certificate
            self.exchange_old_with_new_certificate(new_certificate_name)
            
            # Filter the certificate to find out which one is the older one
            earliest_certificate_iteration_tag = self.get_earliest_certificate_tag()
            earliest_certificate_name = self.get_earliest_certificate_name(earliest_certificate_iteration_tag)

            # Delete the old certificate
            self.delete_old_certificate(earliest_certificate_name=earliest_certificate_name, earliest_certificate_iteration_tag=earliest_certificate_iteration_tag)

        except Exception as e:
            logger.error(f"Unexpected error happened for {self.domain}. Error message: {e}")
            raise   

    ### Different tasks are handled by the below functions that are needed for the execute function ###

    def post_new_certificate(self, vamax_file, new_certificate_name):
        params = {
             "action":"newcert",
             "cert_action":"upload",
             "upload_type":"pem",
             "label": new_certificate_name
        }

        files = {
            "ssl_upload_file": vamax_file
        }

        post_certificate_response = requests.post(url=self.url_ssl_category, params=params, files=files, auth=HTTPBasicAuth(self.username, self.password), verify=False)

        parsed_response = BeautifulSoup(post_certificate_response.text, "html.parser")

        success_message = "SSL Certificate uploaded successfully"

        if parsed_response.select_one("div.information.message div.text") and success_message in parsed_response.get_text():
            logger.debug("Posting certificate was successful")

        else:
            logger.error(f"Couldn't retrieve certificate information")
            raise
    
    def exchange_old_with_new_certificate(self, new_certificate_name):
        params = {
             "action":"edit",
             "applianceSecurityMode":"custom",
             "wui_https_only":"on",
             "wui_https_port":"9443",
             "wui_https_cert": new_certificate_name,
             "wui_https_ciphers":"ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256",
             "go":"Update"
        }

        exchange_certificate_response = requests.post(url=self.url_security_category, params=params, auth=HTTPBasicAuth(self.username, self.password), verify=False)
        
        parsed_response = BeautifulSoup(exchange_certificate_response.text, "html.parser")

        success_message = "Security configuration successfully updated"

        if parsed_response.select_one("div.information.message div.text") and success_message in parsed_response.get_text():
            logger.debug(f"Change old with new certificate was successful")

        else:
            logger.error(f"Couldn't change old with new certificate")
            raise

    def get_earliest_certificate_tag(self):

        # Initialize the date and iteration tag of the older certificate
        earliest_cert_idx = None
        earliest_date = None

        # Iteration tag is set to 0 to start getting the information of the first listed certificate with iteration tag 0
        cert_idx = 0

        # Loop through all certificates returned by the instacnce
        while True:
            params = {
                "t": "cert",
                "v": str(cert_idx)
            }

            # Get the certificate information of the certificate with the current iteration tag
            certificate_response_text = requests.get(url=self.url_get, params=params, auth=HTTPBasicAuth(self.username, self.password), verify=False).text

            # Check if the certificate with the current iteration tag exists
            if f"<label>The SSL Certificate can not be found.</label>" in certificate_response_text:
                break

            # Check if the the certificate has the correct domain tag
            if f"<domain>{self.domain}</domain>" in certificate_response_text:

                # Extract the date when the certificate was issued from the "from" tag
                current_certificate_date = certificate_response_text.split("<from>")[1].split("</from>")[0]
                date_of_issunace = datetime.strptime(current_certificate_date, "%Y-%m-%d %H:%M:%S")

                # Check if there already exists an earliest_date or if the date safed in the variable is newer or older
                if earliest_date is None or date_of_issunace < earliest_date:
                    earliest_date = date_of_issunace
                    earliest_cert_idx = cert_idx

            # Increment the iteration tag to loop through all existing certificates until there is no one left
            cert_idx += 1
            logger.debug(f"The current iteration tag is: {cert_idx}")

        logger.debug(f"Issuance date of oldest certificate: {earliest_date}")
        logger.debug(f"Tag of oldest certificate: {earliest_cert_idx}")

        return earliest_cert_idx
    
    def get_earliest_certificate_name(self, earliest_certificate_iteration_tag):

        # Check if the iteration tag is still initialized with None or was incremented
        if earliest_certificate_iteration_tag is not None:
            params = {
                "t": "cert",
                "v": str(earliest_certificate_iteration_tag)
            }

            # Get the informations from the older certificate
            old_certificate_response = requests.get(url=self.url_get, params=params, auth=HTTPBasicAuth(self.username, self.password), verify=False)

            # Using the "re.search" function to look for a specific pattern in the certificate response text
            # The pattern is designed to extract a certificate name from the URL-like string in "old_certificate_response.text"
            match = re.search(r"certs/(.+?)/", old_certificate_response.text)

            # Check if a match is found
            if match:
                # If a match is found, extract the first capturing group (the text between "certs/" and the next "/")
                earliest_certificate_name = match.group(1)
                logger.debug(f"The old certificate name is: {earliest_certificate_name}")
                 # "earliest_certificate_name" now holds the extracted certificate name

                return earliest_certificate_name

            else:
                logger.error("No match was found")
                raise

        else:
            logger.error(f"No certificates found for domain '{self.domain}'")
            raise
    
    def delete_old_certificate(self, earliest_certificate_name, earliest_certificate_iteration_tag):
        params = {
            "action":"remove",
            "filterunused":"all",
            f"cert_name[{earliest_certificate_iteration_tag}]": earliest_certificate_name
        }

        requests.post(url=self.url_ssl_category, params=params, auth=HTTPBasicAuth(self.username, self.password), verify=False)
        
        params = {
             "action":"remove_confirm",
             "l": "e",
             f"cert_name[{earliest_certificate_iteration_tag}]": earliest_certificate_name
        }

        # Confirm to remove the old certificate
        requests.post(url=self.url_ssl_category, params=params, auth=HTTPBasicAuth(self.username, self.password), verify=False)

    ### Implement this function if you want to work with the VAMax API ###
    #def get_certificate_information(self):
    #   response = requests.post(url=self.url_api, headers=self.headers_get, data=self.data, auth=HTTPBasicAuth(self.username, self.username), verify=False)
    #   return json.loads(response.text)


