# Project Guidelines

## ⚠️ Security Note

Don't store any sensitive values in any of the files! Sensitive informations should be resolved only during runtime using envirnoment variables.

## Coding Guidelines

### Naming Conventions

#### File Naming
- Use `snake_case.py` for Python files
- Example: `certificate_manager.py`, `config_handler.py`

#### Code Naming
- **Variables and Functions**: Use `snake_case`
  - Example: `def process_certificate()`, `certificate_data`
- **Classes and Enums**: Use `PascalCase`
  - Example: `class CertificateManager`, `class ErrorType`
- **Constants**: Use `CAPITAL_SNAKE_CASE`
  - Example: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`

### Variable Naming Best Practices

1. **Be Descriptive**
   - Use meaningful names that describe the purpose
   - Avoid generic names like `data`, `value`, `result`

2. **Collections**
   - Use plural names for collections
   - Examples:
     - `certificates: list[str]`
     - `users: list[dict]`
     - `configurations: dict[str, Any]`

3. **Avoid Type Names**
   - Don't use type names in variable names
   - Bad: `list_of_certificates`, `dict_config`
   - Good: `certificates`, `config`

### Function Guidelines

#### Getters
- Must be read-only functions
- Should not have any side effects
- Should not modify state
- Should be predictable and deterministic

Example:
```python
def get_certificate_status(certificate_id: str) -> str:
    """Returns the current status of a certificate."""
    return certificate_status
```

### Code Organization

1. **Imports**
   - Group imports by type (standard library, third-party, local)
   - Sort alphabetically within each group

2. **Code Documentation**
   - Add comments where necessary
   - Use docstrings for more complex sections

3. **Error Handling**
   - Use appropriate exception types
   - Include meaningful error messages
   - Handle errors at the appropriate level

### Testing Guidelines (not implemented yet)

1. **Test Coverage**
   - Maintain high test coverage
   - Include unit tests for all new functionality
   - Test edge cases and error conditions

2. **Test Naming**
   - Use descriptive test names
   - Follow the pattern: `test_<what>_<condition>_<expected_result>`
   - Example: `test_certificate_renewal_expired_certificate_success`
