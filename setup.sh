#!/bin/bash

# =============================================
# Global Variables and Constants
# =============================================
readonly ENV_TEMPLATE_FILE="env_template.env"
readonly CONFIG_FILE="SSL_Certificate_App/config.json"
readonly HOSTING_PROVIDERS=("AWS (Route 53)" "DigitalOcean" "Cloudflare" "DNSimple" "DNS Made Easy" "Gehirn" "Google Cloud" "Linode" "LuadDNS" "IBM NS1" "OVH" "Sakura Cloud")
readonly PROVIDERS=("nutanix" "rubrik" "hycu" "paloalto" "vsphere" "vamax")

# =============================================
# Functions
# =============================================

print_header() {
    local message="$1"
    local width=50
    local padding=$(( (width - ${#message}) / 2 ))
    printf "|%*s%s%*s|\n" $padding "" "$message" $padding ""
}

print_section() {
    echo ""
    echo "============================================="
    echo "$1"
    echo "============================================="
    echo ""
}

print_subsection() {
    echo ""
    echo "---------------------------------------------"
    echo "$1"
    echo "---------------------------------------------"
    echo ""
}

handle_existing_env_file() {
    while true; do
        if [ -f "$CONFIG_FILE" ]; then
            echo "$CONFIG_FILE file already exists."
            read -p "Do you want to use (u) it or delete (d) it to start over? " USE_OR_DELETE
            echo ""

            case "$USE_OR_DELETE" in
                "u")
                    print_subsection "Keeping existing $CONFIG_FILE file."
                    echo ""
                    read -p "Want to run Certicopter now? (y/n) " RUN_OR_STOP
                    echo ""
                    if [[ "$RUN_OR_STOP" == "y" ]]; then
                        ./run.sh
                    else
                        echo "Exiting..."
                        exit 0
                    fi
                    ;;
                "d")
                    rm -f "$CONFIG_FILE"
                    rm -f "$ENV_TEMPLATE_FILE"
                    print_subsection "Deleted existing files."
                    touch "$CONFIG_FILE"
                    touch "$ENV_TEMPLATE_FILE"
                    return 0
                    ;;
                *)
                    echo "Invalid input. Please enter 'u' or 'd'."
                    echo ""
                    ;;
            esac
        else
            touch "$CONFIG_FILE"
            touch "$ENV_TEMPLATE_FILE"
            print_subsection "Created new $CONFIG_FILE and $ENV_TEMPLATE_FILE files."
            return 0
        fi
    done
}

select_hosting_provider() {
    print_section "Hosting Provider Selection"
    
    while true; do
        echo "Available hosting providers:"
        for i in "${!HOSTING_PROVIDERS[@]}"; do
            echo "  $((i+1))) ${HOSTING_PROVIDERS[$i]}"
        done

        read -p "Enter your hosting provider number: " HOSTING_PROVIDER_CHOICE
        echo ""

        if [[ "$HOSTING_PROVIDER_CHOICE" =~ ^[0-9]+$ ]] && \
           ((HOSTING_PROVIDER_CHOICE >= 1 && HOSTING_PROVIDER_CHOICE <= ${#HOSTING_PROVIDERS[@]})); then
            echo "${HOSTING_PROVIDERS[$HOSTING_PROVIDER_CHOICE-1]}"
            return
        else
            echo "Invalid choice. Please enter a number between 1 and ${#HOSTING_PROVIDERS[@]}."
            echo ""
        fi
    done
}

configure_hosting_provider() {
    local provider="$1"
    
    case "$provider" in
        "AWS (Route 53)")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# AWS Route 53 Configuration
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
EOF
            ;;
        "DigitalOcean")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# DigitalOcean Configuration
DO_AUTH_TOKEN=""
EOF
            ;;
        "Cloudflare")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# Cloudflare Configuration
CF_API_EMAIL=""
CF_API_KEY=""
EOF
            ;;
        "DNSimple")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# DNSimple Configuration
DNSIMPLE_OAUTH_TOKEN=""
EOF
            ;;
        "DNS Made Easy")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# DNS Made Easy Configuration
DNSMADEEASY_API_KEY=""
DNSMADEEASY_API_SECRET=""
EOF
            ;;
        "Gehirn")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# Gehirn Configuration
GEHIRN_API_TOKEN=""
GEHIRN_API_SECRET=""
EOF
            ;;
        "Google Cloud")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# Google Cloud Configuration
GCE_PROJECT=""
GCE_SERVICE_ACCOUNT_FILE=""
EOF
            ;;
        "Linode")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# Linode Configuration
LINODE_API_KEY=""
EOF
            ;;
        "LuadDNS")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# LuaDNS Configuration
LUADNS_API_USERNAME=""
LUADNS_API_TOKEN=""
EOF
            ;;
        "IBM NS1")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# IBM NS1 Configuration
NS1_API_KEY=""
EOF
            ;;
        "OVH")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# OVH Configuration
OVH_ENDPOINT=""
OVH_APPLICATION_KEY=""
OVH_APPLICATION_SECRET=""
OVH_CONSUMER_KEY=""
EOF
            ;;
        "Sakura Cloud")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# Sakura Cloud Configuration
SAKURACLOUD_ACCESS_TOKEN=""
SAKURACLOUD_ACCESS_TOKEN_SECRET=""
EOF
            ;;
    esac
}

configure_provider_system() {
    local provider="$1"
    local system_num="$2"
    
    print_subsection "Configuring system #$system_num for provider: $provider"
    
    case "$provider" in
        "nutanix"|"vsphere"|"vamax")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# $(echo "$provider" | tr '[:lower:]' '[:upper:]') - System ${system_num}
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_DOMAIN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_USERNAME=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_PASSWORD=""
EOF
            ;;
        "paloalto")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# $(echo "$provider" | tr '[:lower:]' '[:upper:]') - System ${system_num}
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_DOMAIN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_API_TOKEN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_PASSPHRASE=""
EOF
            ;;
        "rubrik")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# $(echo "$provider" | tr '[:lower:]' '[:upper:]') - System ${system_num}
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_DOMAIN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_API_TOKEN=""
EOF
            ;;
        "hycu")
            cat >> "$ENV_TEMPLATE_FILE" <<EOF

# $(echo "$provider" | tr '[:lower:]' '[:upper:]') - System ${system_num}
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_DOMAIN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_API_TOKEN=""
$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${system_num}_DNS_IP_ADDRESSES=""
EOF
            ;;
    esac
}

create_config_json() {
    local hosting_provider="$1"
    local notification_email="$2"
    local save_certificates="$3"
    local provider_instances=("${@:4}")

    cat > "$CONFIG_FILE" <<EOF
{
  "certicopter_global_settings": {
    "hosting_provider": "$hosting_provider",
    "notification_email": "$notification_email",
    "save_certificates": "$save_certificates"
  },
  "providers": {
EOF

    local first_provider=true
    for provider_instance in "${provider_instances[@]}"; do
        IFS=':' read -r provider num_instances <<< "$provider_instance"
        
        if [ "$first_provider" = false ]; then
            echo "    }," >> "$CONFIG_FILE"
        fi
        
        echo "    \"$provider\": {" >> "$CONFIG_FILE"
        echo "      \"instances\": [" >> "$CONFIG_FILE"
        
        for ((i=1; i<=num_instances; i++)); do
            echo "        {" >> "$CONFIG_FILE"
            
            case "$provider" in
                "nutanix"|"vsphere"|"vamax")
                    echo "          \"domain_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_DOMAIN\"," >> "$CONFIG_FILE"
                    echo "          \"username_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_USERNAME\"," >> "$CONFIG_FILE"
                    echo "          \"password_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_PASSWORD\"" >> "$CONFIG_FILE"
                    ;;
                "paloalto")
                    echo "          \"domain_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_DOMAIN\"," >> "$CONFIG_FILE"
                    echo "          \"api_token_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_API_TOKEN\"," >> "$CONFIG_FILE"
                    echo "          \"passphrase_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_PASSPHRASE\"" >> "$CONFIG_FILE"
                    ;;
                "rubrik")
                    echo "          \"domain_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_DOMAIN\"," >> "$CONFIG_FILE"
                    echo "          \"api_token_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_API_TOKEN\"" >> "$CONFIG_FILE"
                    ;;
                "hycu")
                    echo "          \"domain_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_DOMAIN\"," >> "$CONFIG_FILE"
                    echo "          \"api_token_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_API_TOKEN\"," >> "$CONFIG_FILE"
                    echo "          \"dns_ip_addresses_env_var\": \"$(echo "$provider" | tr '[:lower:]' '[:upper:]')_SYSTEM_${i}_DNS_IP_ADDRESSES\"" >> "$CONFIG_FILE"
                    ;;
            esac
            
            if [ "$i" -lt "$num_instances" ]; then
                echo "        }," >> "$CONFIG_FILE"
            else
                echo "        }" >> "$CONFIG_FILE"
            fi
        done
        
        echo "      ]" >> "$CONFIG_FILE"
        first_provider=false
    done
    
    echo "    }" >> "$CONFIG_FILE"
    echo "  }" >> "$CONFIG_FILE"
    echo "}" >> "$CONFIG_FILE"
}

# =============================================
# Main Script
# =============================================

# Handle existing environment file
print_section "Environment File Setup"
handle_existing_env_file

# Get hosting provider
select_hosting_provider

# Configure hosting provider
configure_hosting_provider "${HOSTING_PROVIDERS[$HOSTING_PROVIDER_CHOICE-1]}"

# Get notification email
print_section "Notification Settings"
read -p "Enter your notification email address: " GLOBAL_NOTIFICATION_EMAIL
echo ""

# Get certificate saving preference
while true; do
    read -p "Do you want to save the certificates? (y/n): " GLOBAL_SAVE_CERTIFICATES
    echo ""
    
    if [[ "$GLOBAL_SAVE_CERTIFICATES" == "y" || "$GLOBAL_SAVE_CERTIFICATES" == "n" ]]; then
        break
    else
        echo "Invalid input. Please enter 'y' or 'n'."
        echo ""
    fi
done

# Configure providers
print_section "Provider Configuration"
provider_instances=()
for PROVIDER in "${PROVIDERS[@]}"; do
    while true; do
        read -p "Do you use $PROVIDER? (y/n): " USE_PROVIDER
        
        if [[ "$USE_PROVIDER" == "y" ]]; then
            while true; do
                read -p "How many instances do you want to include for $PROVIDER? " NUM_SYSTEMS
                
                if [[ "$NUM_SYSTEMS" =~ ^[1-9]+$ ]]; then
                    provider_instances+=("$PROVIDER:$NUM_SYSTEMS")
                    for ((i=1; i<=NUM_SYSTEMS; i++)); do
                        configure_provider_system "$PROVIDER" "$i"
                    done
                    break
                else
                    echo "Invalid number. Please enter a valid number greater than 0."
                    echo ""
                fi
            done
            break
        elif [[ "$USE_PROVIDER" == "n" ]]; then
            break
        else
            echo "Invalid input. Please enter 'y' or 'n'."
            echo ""
        fi
    done
done

# Create config_test.json
create_config_json "${HOSTING_PROVIDERS[$HOSTING_PROVIDER_CHOICE-1]}" "$GLOBAL_NOTIFICATION_EMAIL" "$GLOBAL_SAVE_CERTIFICATES" "${provider_instances[@]}"

# Final message and script execution
print_section "Setup Complete"
echo "All done! Your template files were created successfully."
echo "The environment template was saved as $ENV_TEMPLATE_FILE"
echo "The configuration file was saved as $CONFIG_FILE"
echo ""
