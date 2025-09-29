#!/bin/bash
# Tesseract OCR Setup Script for All Environments
# Supports macOS, Ubuntu/Debian, CentOS/RHEL, Alpine Linux, and Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ -f /etc/alpine-release ]]; then
        OS="alpine"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    elif [[ -f /etc/redhat-release ]]; then
        OS="rhel"
    else
        OS="unknown"
    fi
}

# Check if running in Docker
is_docker() {
    if [[ -f /.dockerenv ]] || grep -q 'docker\|lxc' /proc/1/cgroup 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Install Tesseract on macOS
install_macos() {
    log_info "Installing Tesseract on macOS..."

    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found. Please install Homebrew first:"
        log_error "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    # Install Tesseract
    if ! brew list tesseract &> /dev/null; then
        log_info "Installing tesseract..."
        brew install tesseract
    else
        log_info "Tesseract already installed"
    fi

    # Install language packs
    if ! brew list tesseract-lang &> /dev/null; then
        log_info "Installing tesseract language packs..."
        brew install tesseract-lang
    else
        log_info "Tesseract language packs already installed"
    fi

    log_success "Tesseract installed successfully on macOS"
}

# Install Tesseract on Debian/Ubuntu
install_debian() {
    log_info "Installing Tesseract on Debian/Ubuntu..."

    # Update package list
    log_info "Updating package list..."
    sudo apt-get update -qq

    # Install Tesseract and language packs
    log_info "Installing tesseract and language packs..."
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-tha

    # Install additional useful languages
    sudo apt-get install -y tesseract-ocr-chi-sim tesseract-ocr-jpn tesseract-ocr-kor || true

    log_success "Tesseract installed successfully on Debian/Ubuntu"
}

# Install Tesseract on RHEL/CentOS
install_rhel() {
    log_info "Installing Tesseract on RHEL/CentOS..."

    # Install EPEL repository if not already available
    if ! yum repolist | grep -q epel; then
        log_info "Installing EPEL repository..."
        sudo yum install -y epel-release
    fi

    # Install Tesseract
    log_info "Installing tesseract..."
    sudo yum install -y tesseract tesseract-langpack-eng tesseract-langpack-tha

    # Install additional languages if available
    sudo yum install -y tesseract-langpack-chi_sim tesseract-langpack-jpn tesseract-langpack-kor || true

    log_success "Tesseract installed successfully on RHEL/CentOS"
}

# Install Tesseract on Alpine Linux
install_alpine() {
    log_info "Installing Tesseract on Alpine Linux..."

    # Update package index
    log_info "Updating package index..."
    apk update

    # Install Tesseract and language packs
    log_info "Installing tesseract and language packs..."
    apk add tesseract-ocr tesseract-ocr-data-eng tesseract-ocr-data-tha

    # Install additional languages if available
    apk add tesseract-ocr-data-chi_sim tesseract-ocr-data-jpn tesseract-ocr-data-kor || true

    log_success "Tesseract installed successfully on Alpine Linux"
}

# Verify Tesseract installation
verify_installation() {
    log_info "Verifying Tesseract installation..."

    # Check if tesseract command is available
    if ! command -v tesseract &> /dev/null; then
        log_error "Tesseract not found in PATH"
        exit 1
    fi

    # Get version
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    log_info "Found: $TESSERACT_VERSION"

    # Check available languages
    log_info "Available languages:"
    tesseract --list-langs 2>/dev/null | tail -n +2 | while read lang; do
        case $lang in
            eng) log_info "  ✓ English ($lang)" ;;
            tha) log_info "  ✓ Thai ($lang)" ;;
            chi_sim) log_info "  ✓ Chinese Simplified ($lang)" ;;
            jpn) log_info "  ✓ Japanese ($lang)" ;;
            kor) log_info "  ✓ Korean ($lang)" ;;
            *) log_info "  - $lang" ;;
        esac
    done

    # Check required languages
    if tesseract --list-langs 2>/dev/null | grep -q "eng"; then
        log_success "English language pack found"
    else
        log_warning "English language pack not found"
    fi

    if tesseract --list-langs 2>/dev/null | grep -q "tha"; then
        log_success "Thai language pack found"
    else
        log_warning "Thai language pack not found"
    fi
}

# Test OCR functionality
test_ocr() {
    log_info "Testing OCR functionality..."

    # Create a simple test image with text (requires ImageMagick)
    if command -v convert &> /dev/null; then
        TEST_IMAGE="/tmp/tesseract_test.png"
        convert -size 300x100 xc:white -font Arial -pointsize 24 -fill black \
                -annotate +10+50 "Hello World 123" "$TEST_IMAGE" 2>/dev/null || {
            log_warning "Could not create test image (ImageMagick not available)"
            return 0
        }

        # Test English OCR
        if tesseract "$TEST_IMAGE" stdout 2>/dev/null | grep -q "Hello"; then
            log_success "English OCR test passed"
        else
            log_warning "English OCR test failed"
        fi

        # Cleanup
        rm -f "$TEST_IMAGE"
    else
        log_info "Skipping OCR test (ImageMagick not available)"
    fi
}

# Create configuration file
create_config() {
    log_info "Creating Tesseract configuration..."

    # Create tessdata directory if it doesn't exist
    TESSDATA_DIR="/usr/local/share/tessdata"
    if [[ "$OS" == "macos" ]]; then
        TESSDATA_DIR="/opt/homebrew/share/tessdata"
    fi

    # Create environment configuration
    cat > /tmp/tesseract_env.sh << EOF
# Tesseract OCR Environment Configuration
export TESSDATA_PREFIX="$TESSDATA_DIR"
export TESSERACT_PATH="\$(which tesseract)"

# Verify Tesseract is available
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract not found in PATH"
fi

# Show available languages
alias tesseract-langs="tesseract --list-langs"

# Common OCR commands
alias ocr-eng="tesseract - stdout -l eng"
alias ocr-tha="tesseract - stdout -l tha"
alias ocr-multi="tesseract - stdout -l eng+tha"
EOF

    log_info "Environment configuration created at /tmp/tesseract_env.sh"
    log_info "To use: source /tmp/tesseract_env.sh"
}

# Main installation function
main() {
    echo "🔍 Tesseract OCR Setup for Poon AI Service"
    echo "=========================================="

    # Detect environment
    detect_os
    log_info "Detected OS: $OS"

    if is_docker; then
        log_info "Running in Docker container"
    fi

    # Install based on OS
    case $OS in
        macos)
            install_macos
            ;;
        debian)
            install_debian
            ;;
        rhel)
            install_rhel
            ;;
        alpine)
            install_alpine
            ;;
        *)
            log_error "Unsupported OS: $OS"
            log_error "Please install Tesseract manually:"
            log_error "  - Install tesseract-ocr package"
            log_error "  - Install eng and tha language packs"
            exit 1
            ;;
    esac

    # Verify installation
    verify_installation

    # Test OCR
    test_ocr

    # Create configuration
    create_config

    echo ""
    log_success "Tesseract OCR setup completed successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Restart your terminal or run: source /tmp/tesseract_env.sh"
    echo "2. Test the AI service OCR functionality"
    echo "3. Upload receipt images to test Thai + English OCR"
    echo ""
    echo "📖 Usage examples:"
    echo "  tesseract image.png stdout -l eng     # English only"
    echo "  tesseract image.png stdout -l tha     # Thai only"
    echo "  tesseract image.png stdout -l eng+tha # Both languages"
}

# Run main function
main "$@"
