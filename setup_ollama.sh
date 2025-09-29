#!/bin/bash

# Setup script for Ollama with Llama 3.2 3B model
# This script installs Ollama and sets up the required model for local AI processing

set -e

echo "🦙 Setting up Ollama with Llama 3.2 for local AI processing..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo "📱 Detected platform: $PLATFORM"

# Install Ollama if not already installed
if command_exists ollama; then
    echo "✅ Ollama is already installed"
    ollama --version
else
    echo "📥 Installing Ollama..."

    if [[ "$PLATFORM" == "macos" ]]; then
        # Install via Homebrew if available, otherwise use curl
        if command_exists brew; then
            echo "🍺 Installing via Homebrew..."
            brew install ollama
        else
            echo "📥 Installing via curl..."
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    else
        # Linux installation
        echo "🐧 Installing on Linux..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi

    echo "✅ Ollama installed successfully"
fi

# Start Ollama service
echo "🚀 Starting Ollama service..."

if [[ "$PLATFORM" == "macos" ]]; then
    # On macOS, start as a background service
    if ! pgrep -f "ollama serve" > /dev/null; then
        echo "Starting Ollama server in background..."
        nohup ollama serve > ollama.log 2>&1 &
        sleep 3
    else
        echo "✅ Ollama server is already running"
    fi
else
    # On Linux, check if systemd service exists
    if systemctl is-active --quiet ollama; then
        echo "✅ Ollama service is already running"
    else
        echo "Starting Ollama service..."
        sudo systemctl start ollama
        sudo systemctl enable ollama
    fi
fi

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Check if Ollama is responding
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama is not responding after 60 seconds"
    echo "Please check the logs and try running 'ollama serve' manually"
    exit 1
fi

# Pull Llama 3.2 3B model
echo "📥 Pulling Llama 3.2 3B model (this may take a while)..."
echo "Model size: ~2GB - please ensure you have sufficient disk space and internet bandwidth"

if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ Llama 3.2 3B model is already available"
else
    echo "⬇️ Downloading Llama 3.2 3B model..."
    ollama pull llama3.2:3b

    if [ $? -eq 0 ]; then
        echo "✅ Llama 3.2 3B model downloaded successfully"
    else
        echo "❌ Failed to download Llama 3.2 3B model"
        echo "You can try downloading it manually with: ollama pull llama3.2:3b"
        exit 1
    fi
fi

# Test the model
echo "🧪 Testing the model..."
echo "Running a simple test to ensure the model works correctly..."

TEST_RESPONSE=$(ollama run llama3.2:3b "Parse this spending: coffee 120 baht. Return only JSON with amount, merchant, category." --format json 2>/dev/null || echo "")

if [[ -n "$TEST_RESPONSE" ]]; then
    echo "✅ Model test successful!"
    echo "Sample response: $TEST_RESPONSE"
else
    echo "⚠️ Model test failed, but model is installed"
    echo "You may need to test it manually with: ollama run llama3.2:3b"
fi

# Show available models
echo "📋 Available models:"
ollama list

# Configuration summary
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Configuration Summary:"
echo "- Ollama Server: http://localhost:11434"
echo "- Model: llama3.2:3b"
echo "- Status: Ready for AI processing"
echo ""
echo "Next steps:"
echo "1. Start your AI service: python main.py"
echo "2. The service will automatically connect to Ollama"
echo "3. Test the API endpoints for spending text parsing"
echo ""
echo "Useful commands:"
echo "- Check Ollama status: curl http://localhost:11434/api/tags"
echo "- Test model directly: ollama run llama3.2:3b 'Hello'"
echo "- Stop Ollama: pkill -f 'ollama serve' (macOS) or sudo systemctl stop ollama (Linux)"
echo ""

# Create a simple health check script
cat > check_ollama_health.sh << 'EOF'
#!/bin/bash
# Simple health check for Ollama service

echo "🔍 Checking Ollama health..."

# Check if service is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama service is not running"
    echo "Start it with: ollama serve"
    exit 1
fi

# Check if model is available
if ollama list | grep -q "llama3.2:3b"; then
    echo "✅ Ollama service is healthy"
    echo "✅ Llama 3.2 3B model is available"
    echo "🚀 Ready for AI processing!"
else
    echo "⚠️ Ollama is running but Llama 3.2 3B model is missing"
    echo "Download it with: ollama pull llama3.2:3b"
fi
EOF

chmod +x check_ollama_health.sh
echo "📄 Created health check script: ./check_ollama_health.sh"

echo ""
echo "🦙 Ollama setup completed! Your local AI is ready to process spending entries."
