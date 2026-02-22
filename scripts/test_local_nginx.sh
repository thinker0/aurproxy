#!/bin/bash
set -e

# Configuration
NGINX_BIN="/opt/homebrew/opt/nginx/bin/nginx"
# Example JSON config file
CONF_FILE="./scripts/aurproxy-local-test.json"
MANAGEMENT_PORT=8081
BACKEND="nginx"
PEX_FILE="./aurproxy_mac.pex"

# Build temporary directory
TMP_DIR="$(pwd)/tmp/nginx"
mkdir -p "$TMP_DIR/logs"
mkdir -p "$TMP_DIR/conf"

NGINX_CONFIG_DEST="$TMP_DIR/conf/nginx.conf"
NGINX_PID_PATH="$TMP_DIR/nginx.pid"

echo "--------------------------------------------------"
echo "Local Nginx Test Script (PEX mode)"
echo "--------------------------------------------------"

# 1. Build Mac PEX if it doesn't exist
if [ ! -f "$PEX_FILE" ]; then
    echo "[0/3] Building Mac PEX (Python 3.9)..."
    # Ensure pex is installed in the current environment
    python3 -m pip install -q pex wheel setuptools
    
    # Cleanup metadata
    python3 -c 'import os, shutil; [os.remove(os.path.join(r, f)) for r, d, fs in os.walk(".") for f in fs if f == ".DS_Store" or f.endswith(".pyc")]; [shutil.rmtree(os.path.join(r, d)) for r, ds, f in os.walk(".") for d in ds if d == "__pycache__"]'
    
    # Build PEX
    mkdir -p build_src
    cp -r tellapart build_src/
    cp -r templates build_src/
    python3 -m pex -D build_src -r requirements.txt -m tellapart.aurproxy.command -o "$PEX_FILE" --python=python3 --disable-cache
    rm -rf build_src
    echo "PEX built successfully: $PEX_FILE"
fi

# 2. Run aurproxy setup using PEX
echo "[1/3] Running aurproxy setup..."
$PEX_FILE run \
  --management-port $MANAGEMENT_PORT \
  --config "file://$CONF_FILE" \
  --backend $BACKEND \
  --setup

# 3. Start Nginx
echo "[2/3] Starting Nginx..."
if [ -f "$NGINX_PID_PATH" ]; then
    kill $(cat "$NGINX_PID_PATH") 2>/dev/null || true
fi
$NGINX_BIN -c "$NGINX_CONFIG_DEST" -g "pid $NGINX_PID_PATH; error_log $TMP_DIR/logs/error.log;"

# 4. Start aurproxy in the foreground
echo "[3/3] Starting aurproxy..."
$PEX_FILE run \
  --management-port $MANAGEMENT_PORT \
  --config "file://$CONF_FILE" \
  --backend $BACKEND
