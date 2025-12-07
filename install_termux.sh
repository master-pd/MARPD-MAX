#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 MARPd ULTRA PRO MAX - Termux Installation"
echo "============================================="

# Update packages
pkg update -y
pkg upgrade -y

# Install Python
pkg install -y python python-pip

# Install system dependencies
pkg install -y git wget curl termux-api
pkg install -y libjpeg-turbo libpng
pkg install -y openssl libffi
pkg install -y clang make cmake
pkg install -y rust binutils

# Install Python build dependencies
pip install --upgrade pip setuptools wheel

# Create virtual environment (optional but recommended)
python -m venv marpd-env
source marpd-env/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install --no-cache-dir -r requirements.txt

# Fix common Termux issues
echo "🔧 Fixing Termux-specific issues..."

# Fix PIL/Pillow issue
pip uninstall -y Pillow
LDFLAGS="-L/system/lib64" CFLAGS="-I/data/data/com.termux/files/usr/include" pip install Pillow --no-binary :all:

# Fix cryptography issue
pkg install -y rust
CARGO_BUILD_TARGET=aarch64-linux-android pip install cryptography

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs backups cache media

# Set permissions
chmod 755 data logs backups cache media

# Test installation
echo "✅ Testing installation..."
python -c "import telegram; import psutil; print('🎉 All packages installed successfully!')"

echo ""
echo "🚀 Installation Complete!"
echo "📁 Project location: $(pwd)"
echo "🐍 Python: $(python --version)"
echo "📦 PIP: $(pip --version)"
echo ""
echo "🛠️ To start the bot:"
echo "  python main.py"
echo ""
echo "💡 Tips for Termux:"
echo "  1. Keep Termux in background (disable battery optimization)"
echo "  2. Use 'termux-wake-lock' to prevent sleep"
echo "  3. Use 'termux-notification' for alerts"
echo "  4. Backup regularly: 'python main.py' -> Backup option"
