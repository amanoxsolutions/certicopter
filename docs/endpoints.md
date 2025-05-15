# API Endpoints Documentation

This document provides a comprehensive overview of all API endpoints used in the Certicopter project for managing SSL certificates across different systems.

## Nutanix Endpoints

### Base URL
```
https://{domain}:9440
```

### Endpoints

1. **Get Certificate Information**
   - **URL**: `/PrismGateway/services/rest/v1/keys/pem`
   - **Method**: GET
   - **Headers**:
     - `Accept: application/json`
     - `Content-Type: application/json`
     - `Authorization: Basic {base64_encoded_credentials}`
   - **Purpose**: Retrieves current certificate information

2. **Import New Certificate**
   - **URL**: `/PrismGateway/services/rest/v1/keys/pem/import`
   - **Method**: POST
   - **Headers**:
     - `Accept: application/json`
     - `Content-Type: multipart/form-data`
     - `Authorization: Basic {base64_encoded_credentials}`
   - **Body**: Form data with:
     - `keyType: RSA_2048`
     - `key`: Private key file
     - `cert`: Certificate file
     - `caChain`: CA chain file
   - **Purpose**: Imports a new SSL certificate

## Palo Alto Networks Endpoints

### Base URL
```
https://{domain}/api
```

### Endpoints

1. **Get Certificate Information**
   - **URL**: `/api`
   - **Method**: GET
   - **Parameters**:
     - `key`: API token
     - `type`: config
     - `action`: get
     - `xpath`: /config/shared/certificate
   - **Purpose**: Retrieves current certificate information

2. **Import Certificate**
   - **URL**: `/api`
   - **Method**: POST
   - **Parameters**:
     - `key`: API token
     - `type`: import
     - `category`: keypair
     - `certificate-name`: {certificate_name}
     - `format`: pem
     - `passphrase`: {passphrase}
   - **Files**: Certificate file
   - **Purpose**: Imports a new SSL certificate

3. **Update Certificate**
   - **URL**: `/api`
   - **Method**: POST
   - **Parameters**:
     - `key`: API token
     - `type`: config
     - `action`: set
     - `xpath`: /config/shared/ssl-tls-service-profile/entry[@name='letsencrypt']
   - **Purpose**: Updates the SSL/TLS service profile with new certificate

4. **Delete Certificate**
   - **URL**: `/api`
   - **Method**: POST
   - **Parameters**:
     - `key`: API token
     - `type`: config
     - `action`: delete
     - `xpath`: /config/shared/certificate/entry[@name='{certificate_name}']
   - **Purpose**: Deletes an old certificate

5. **Commit Changes**
   - **URL**: `/api`
   - **Method**: GET
   - **Parameters**:
     - `key`: API token
     - `type`: "commit",
     - `cmd`: <commit></commit>
   - **Purpose**: Commits all configuration changes

## VMware vSphere Endpoints

### Base URL
```
https://{domain}
```

### Endpoints

1. **Create Session**
   - **URL**: `/api/session`
   - **Method**: POST
   - **Headers**:
     - `Accept: application/json`
     - `Content-Type: application/json`
     - `Authorization: Base {base64_encoded_credentials}`
   - **Purpose**: Creates a new session and returns session ID

2. **Update Certificate**
   - **URL**: `/api/vcenter/certificate-management/vcenter/tls`
   - **Method**: PUT
   - **Headers**:
     - `vmware-api-session-id`: {session_id}
   - **Body**: JSON with:
     - `cert`: Certificate file content
     - `key`: Private key file content
     - `root_cert`: Root certificate file content
   - **Purpose**: Updates the vCenter TLS certificate

## Rubrik Endpoints

### Base URL
```
https://{domain}
```

### Endpoints

1. **Get Certificates**
   - **URL**: `/api/v1/certificate`
   - **Method**: GET
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Purpose**: Retrieves all certificates

2. **Create Certificate**
   - **URL**: `/api/v1/certificate`
   - **Method**: POST
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Body**: JSON with:
     - `hasKey`: true
     - `name`: {certificate_name}
     - `pemFile`: Certificate file content
     - `privateKey`: Private key file content
   - **Purpose**: Creates a new certificate

3. **Update Cluster Settings**
   - **URL**: `/api/v1/cluster/me/security/web_signed_cert`
   - **Method**: PUT
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Body**: JSON with:
     - `certificateId`: {new_certificate_id}
   - **Purpose**: Updates the cluster's web certificate

4. **Delete Certificate**
   - **URL**: `/api/v1/certificate/{certificate_id}`
   - **Method**: DELETE
   - **Headers**:
     - `Authorization: Bearer {api_token}`
   - **Purpose**: Deletes a certificate

## HYCU Endpoints

### Base URL
```
https://{domain}:8443
```

### Endpoints

1. **Get Network Information**
   - **URL**: `/rest/v1.0/networks`
   - **Method**: GET
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Purpose**: Retrieves network configuration

2. **Get Certificates**
   - **URL**: `/rest/v1.0/certificate`
   - **Method**: GET
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Purpose**: Retrieves all certificates

3. **Create Certificate**
   - **URL**: `/rest/v1.0/certificate`
   - **Method**: POST
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Body**: JSON with:
     - `name`: {certificate_name}
     - `privateKey`: Private key file content
     - `certificate`: Certificate file content
   - **Purpose**: Creates a new certificate

4. **Update Network Certificate**
   - **URL**: `/rest/v1.0/networks/{uuid}`
   - **Method**: PATCH
   - **Headers**:
     - `Authorization: Bearer {api_token}`
     - `Content-Type: application/json`
   - **Body**: JSON with:
     - `dns`: {dns_ip_addresses}
     - `certificateUuid`: {new_certificate_id}
   - **Purpose**: Updates the network's SSL certificate

5. **Delete Certificate**
   - **URL**: `/rest/v1.0/certificate/{certificate_id}`
   - **Method**: DELETE
   - **Headers**:
     - `Authorization: Bearer {api_token}`
   - **Purpose**: Deletes a certificate

## VAMax Loadbalancer Endpoints

### Base URL
```
https://{domain}:9443
```

### Endpoints

1. **Get Certificate Information**
   - **URL**: `/lbadmin/ajax/get_ssl.php`
   - **Method**: GET
   - **Parameters**:
     - `t`: "cert"
     - `v`: {certificate_index}
   - **Authentication**: Basic Auth
   - **Purpose**: Retrieves certificate information for a specific index

2. **Upload New Certificate**
   - **URL**: `/lbadmin/config/sslcert.php`
   - **Method**: POST
   - **Parameters**:
     - `action`: "newcert"
     - `cert_action`: "upload"
     - `upload_type`: "pem"
     - `label`: {certificate_name}
   - **Files**:
     - `ssl_upload_file`: Certificate file
   - **Authentication**: Basic Auth
   - **Purpose**: Uploads a new SSL certificate

3. **Update Security Settings**
   - **URL**: `/lbadmin/config/secure.php`
   - **Method**: POST
   - **Parameters**:
     - `action`: "edit"
     - `applianceSecurityMode`: "custom"
     - `wui_https_only`: "on"
     - `wui_https_port`: "9443"
     - `wui_https_cert`: {certificate_name}
     - `wui_https_ciphers`: "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256"
     - `go`: "Update"
   - **Authentication**: Basic Auth
   - **Purpose**: Updates the security settings with new certificate

4. **Delete Certificate**
   - **URL**: `/lbadmin/config/sslcert.php`
   - **Method**: POST
   - **Parameters**:
     - `action`: "remove"
     - `filterunused`: "all"
     - `cert_name[{certificate_index}]`: {certificate_name}
   - **Authentication**: Basic Auth
   - **Purpose**: Initiates certificate deletion

5. **Confirm Certificate Deletion**
   - **URL**: `/lbadmin/config/sslcert.php`
   - **Method**: POST
   - **Parameters**:
     - `action`: "remove_confirm"
     - `l`: "e"
     - `cert_name[{certificate_index}]`: {certificate_name}
   - **Authentication**: Basic Auth
   - **Purpose**: Confirms and completes certificate deletion

## Common Authentication Methods

1. **Basic Authentication**
   - Used by: Nutanix, vSphere, VAMax Loadbalancer
   - Format: `Basic {base64_encoded_username:password}`

2. **Bearer Token Authentication**
   - Used by: Rubrik, HYCU
   - Format: `Bearer {api_token}`

3. **API Key Authentication**
   - Used by: Palo Alto Networks
   - Format: URL parameter `key={api_token}`

## Common Response Codes

- `200`: Success
- `201`: Created
- `202`: Accepted
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error 