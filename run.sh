#!/bin/bash

# =============================================
# Variables
# =============================================
NONINTERACTIVE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --noninteractive)
            NONINTERACTIVE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================
# Functions
# =============================================

print_header() {
    local message="$1"
    local width=51
    local max_length=$((width - 1))  # Account for the frame borders
    local indent=2  # Number of spaces for indentation
    
    # If message is empty, just print an empty line
    if [ -z "$message" ]; then
        printf "|%*s|\n" $width ""
        return
    fi
    
    # Split message into words
    read -ra words <<< "$message"
    local current_line=""
    local is_first_line=true
    
    for word in "${words[@]}"; do
        # If adding this word would exceed the line length, print current line and start new one
        if [ $((${#current_line} + ${#word} + 1)) -gt $max_length ]; then
            # Print the current line
            if [ "$is_first_line" = true ]; then
                printf "| %-*s|\n" $max_length "$current_line"
                is_first_line=false
            else
                printf "| %*s%-*s|\n" $indent "" $((max_length - indent)) "$current_line"
            fi
            current_line="$word"
        else
            # Add word to current line
            if [ -z "$current_line" ]; then
                current_line="$word"
            else
                current_line="$current_line $word"
            fi
        fi
    done
    
    # Print any remaining text
    if [ ! -z "$current_line" ]; then
        if [ "$is_first_line" = true ]; then
            printf "| %-*s|\n" $max_length "$current_line"
        else
            printf "| %*s%-*s|\n" $indent "" $((max_length - indent)) "$current_line"
        fi
    fi
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

# =============================================
# Main Script
# =============================================

# Print welcome message
echo "|===================================================|"
print_header "Certicopter: You now started the setup process..."
print_header ""
print_header "#### Reminder ####"
print_header ""
print_header "Check if the following requirements are met:"
print_header ""
print_header "- Docker engine installed"
print_header "- Domain registered at one of the available hosting providers"
print_header "- Executed the setup.sh script"
print_header "- Access keys for the provider set in your environment variables as well as all credentials to access the systems you want to exchange certificates for"
print_header "- Correct access rights set for the container to access the environment variables and the connections to the systems for certificate exchange"
echo "|===================================================|"
echo ""

# Check config file
config="SSL_Certificate_App/config.json"

if [ "$NONINTERACTIVE" = false ]; then
    echo "Please first validate the values in the $config file before continuing."
    echo "Did you configure all environment variables correctly?"
    echo ""

    read -n 1 -s -r -p "Press any key to output the $config file: "
    echo ""

    echo "##############################################"
    echo ""
    cat "$config"
    echo ""
    echo "##############################################"
    echo ""

    # Confirm execution
    while true; do
        read -p "Are all the values correct? Do you want to run the script now? (y/n): " RUN_SCRIPT_CONFIRM
        echo ""

        case "$RUN_SCRIPT_CONFIRM" in
            "y")
                print_section "Script Execution"
                echo "Script will be executed now..."
                echo ""
                docker compose up --build
                break
                ;;
            "n")
                print_section "Script Termination"
                echo "Script will not be executed."
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid input. Please enter 'y' or 'n'."
                echo ""
                ;;
        esac
    done
else
    print_section "Script Execution"
    echo "Running in non-interactive mode..."
    echo ""
    docker compose up --build
fi
