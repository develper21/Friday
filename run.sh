#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                    JEAN MAX - VOICE ASSISTANT DAEMON                       ║
# ║                    Advanced AI-Powered Personal Assistant                  ║
# ╚════════════════════════════════════════════════════════════════════════════╝

# ANSI Color Codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
RESET='\033[0m'

# Spinner characters for animations
SPINNER="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Print ASCII Art Header
print_header() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    ██╗  ██╗██╗███╗   ███╗██████╗ ███████╗██████╗ 
    ██║  ██║██║████╗ ████║██╔══██╗██╔════╝██╔══██╗
    ███████║██║██╔████╔██║██████╔╝█████╗  ██████╔╝
    ██╔══██║██║██║╚██╔╝██║██╔══██╗██╔══╝  ██╔══██╗
    ██║  ██║██║██║ ╚═╝ ██║██████╔╝███████╗██║  ██║
    ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚═════╝╚══════╝╚═╝  ╚═╝
EOF
    echo -e "${RESET}"
    echo -e "${BOLD}${WHITE}                    Advanced AI Voice Assistant${RESET}"
    echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════════${RESET}"
    echo ""
}

# Animated loading function
animate_loading() {
    local message="$1"
    local duration=${2:-3}
    
    echo -ne "${YELLOW}⏳ ${message}${RESET}"
    for i in $(seq 1 $duration); do
        for j in $(seq 1 10); do
            echo -ne "\r${YELLOW}⏳ ${message} ${SPINNER:j%10:1}${RESET}"
            sleep 0.1
        done
    done
    echo -ne "\r${GREEN}✓ ${message}${RESET}\n"
}

# Print section header
print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}▶ $1${RESET}"
    echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${RESET}"
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

# Print error message
print_error() {
    echo -e "${RED}✗ $1${RESET}"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${RESET}"
}

# Print info message
print_info() {
    echo -e "${CYAN}ℹ $1${RESET}"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Print header
print_header

# Check if virtual environment exists
print_section "Environment Setup"
if [ ! -d "venv" ]; then
    print_info "Virtual environment not found. Creating..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment found"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    print_info "Installing dependencies..."
    pip install -r requirements.txt -q
    if [ $? -eq 0 ]; then
        touch venv/.installed
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
else
    print_success "Dependencies already installed"
fi

# Copy config to user config directory if not exists
print_section "Configuration Setup"
CONFIG_DIR="$HOME/.config/voice_assistant"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    print_info "Creating config directory..."
    mkdir -p "$CONFIG_DIR"
    cp config/config.json "$CONFIG_DIR/config.json"
    print_success "Config created at ${CYAN}$CONFIG_DIR/config.json${RESET}"
    print_warning "Edit this file to configure your audio device"
else
    print_success "Configuration found at ${CYAN}$CONFIG_DIR/config.json${RESET}"
fi

# System check
print_section "System Check"
print_info "Python version: $(python3 --version)"
print_info "Working directory: ${CYAN}$(pwd)${RESET}"

# Final startup
print_section "Starting Jean Max"
echo -e "${MAGENTA}╔══════════════════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${MAGENTA}║${RESET} ${BOLD}${WHITE}Jean Max Voice Assistant is initializing...${RESET}                                  ${MAGENTA}║${RESET}"
echo -e "${MAGENTA}╚══════════════════════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# Run the assistant daemon
python assistance/main.py
