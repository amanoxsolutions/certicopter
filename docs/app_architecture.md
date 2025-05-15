# Code Structure Documentation

## Overview
Certicopter is a Python-based automation tool designed to manage and renew SSL certificates across multiple systems. The project follows a modular architecture with clear separation of concerns and a plugin-based approach for different system integrations.

## Core Components

### 1. Application Entry Point

- **File**: `app_starter.py`
- **Purpose**: Main entry point of the application

### 2. System-Specific Executors

Each supported system has its own executor class implementing the CertificateManager interface:

#### {system}_executor.py structure

1. **{Provider}CertificateManager** class

This class initializes all the parameters/variables that are needed in the function multiple times and everytime a new instance should receive a certificate a new object gets created from the loop in the "renew_system_certificates.py" file.

2. **execute_certificate_renewal** function

This function coordinates all other functions that are needed for the renewal of the certificate in one instance and therefore includes the whole "logic" of a provider certificate renewal.

3. **get_required_parameters** function

Is a static method which is used to retrieve the needed configuration parameters from the config.json.

4. All other functions

Fulfill a specific task in the renewal process (depending on the providers specific requirements) and get called or executed by the "execute_certificate_renewal" function.

The project uses a plugin-based kind of architecture with separate executor files for each supported system:

#### Nutanix Executor
- **File**: `nutanix_executor.py`
- **Purpose**: Manages certificates for Nutanix clusters

#### Palo Alto Networks Executor
- **File**: `paloalto_executor.py`
- **Purpose**: Manages certificates for Palo Alto firewalls

#### VMware vSphere Executor
- **File**: `vsphere_executor.py`
- **Purpose**: Manages certificates for vSphere environments

#### Rubrik Executor
- **File**: `rubrik_executor.py`
- **Purpose**: Manages certificates for Rubrik CDM

#### HYCU Executor
- **File**: `hycu_executor.py`
- **Purpose**: Manages certificates for HYCU SaaS

#### VAMax Loadbalancer Executor
- **File**: `vamax_executor.py`
- **Purpose**: Manages certificates for VAMax loadbalancers$

### 3. Utility Modules

#### Certificate Utilities
- **File**: `certbot_utils.py`
- **Purpose**: Provides helper functions for certificate operations
- **Key Functions**:
  - Certificate generation
  - Certificate validation
  - Certificate file management
  - Certificate concatenation

#### Certificate Renewal
- **File**: `renew_system_certificates.py`
- **Purpose**: Core functionality for certificate renewal
- **Key Functions**:
  - Renewal workflow management
  - Certificate validation
  - Certificate deployment

### 4. Certificate Management Interface
- **File**: `certificatemanager_abc.py`
- **Purpose**: Defines the interface for all certificate managers
- **Key Components**:
  - Abstract Base Class (ABC) defining required methods
  - Standard interface for certificate operations
  - Ensures consistent behavior across different systems

### 5. Main Configuration
- **File**: `config.json`
- **Purpose**: Configuration of global variables
- **Key Components**:
  - Global variables
  - Providers
  - Instances
  - Environment variables

### 6. Requirements Files

#### `requirements.txt`
- Core dependencies
- Essential packages needed for basic functionality

#### `requirements_dev.txt`
- Additional dependencies
- Tools and packages needed for development

### 7. Testing and Validation

#### Unit Testing (in progress)
1. **Test Directory**
   - Individual component tests
   - Mock implementations
   - Test utilities

2. **Test Coverage**
   - Core functionality
   - Edge cases
   - Error conditions

#### Integration Testing
1. **System Integration**
   - End-to-end testing
   - API integration
   - Certificate validation

2. **Environment Testing**
   - Development environment
   - Staging environment
   - Production environment

### 8. Logging System
1. **Log Levels**
   - DEBUG: Detailed debugging information
   - INFO: General operational information
   - WARNING: Warning messages
   - ERROR: Error messages
   - CRITICAL: Critical system failures

2. **Log Outputs**
   - File logging (`app_certicopter.log`)
   - Console output
   - System logging (if configured)

## Architecture Principles

1. **Modularity**: Each system integration is implemented as a separate module
2. **Extensibility**: New system integrations can be added with creating a new executor file
3. **Configuration Management**: Clear separation between core and local configurations
4. **Logging**: Comprehensive logging system for debugging and monitoring
5. **Error Handling**: Robust error handling across all modules

## Application Workflow

### 1. Initialization Phase
1. Application starts via `app_starter.py`
2. Configuration is loaded from `config.json`
3. Logging system is initialized at the beginning of each file
4. Appropriate executor is selected based on configuration

### 2. Certificate Renewal Phase
1. Looping through different providers and instances
2. Certificate files are prepared and formatted according to system requirements
3. Certificate information is retrieved if necessary
4. New certificate is deployed to the target system
5. Old certificate is removed (if applicable)
6. Changes are committed (if required by the system)

### 3. Cleanup Phase
1. Temporary files are removed
2. Logs are updated
3. Status is reported