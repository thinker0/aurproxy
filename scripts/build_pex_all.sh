#!/bin/bash
set -e

# Usage helper
usage() {
    echo "Usage: $0 [7|8|9|all]"
    echo "  7   : Build for CentOS 7 (aurproxy-7.pex)"
    echo "  8   : Build for Rocky Linux 8 (aurproxy-8.pex)"
    echo "  9   : Build for Rocky Linux 9 (aurproxy-9.pex)"
    echo "  all : Build all versions"
    exit 1
}

# Function to build specific version
build_target() {
    VERSION=$1
    case $VERSION in
        7)
            DOCKERFILE="scripts/Dockerfile.centos"
            TAG="aurproxy-centos7"
            OUT="aurproxy-7.pex"
            SRC_OUT="aurproxy-7.pex"
            ;;
        8)
            DOCKERFILE="scripts/Dockerfile.rocky8"
            TAG="aurproxy-rocky8"
            OUT="aurproxy-8.pex"
            SRC_OUT="aurproxy-8.pex"
            ;;
        9)
            DOCKERFILE="scripts/Dockerfile.rocky9"
            TAG="aurproxy-9"
            OUT="aurproxy-9.pex"
            SRC_OUT="aurproxy-9.pex"
            ;;
        *)
            return
            ;;
    esac

    echo "--------------------------------------------------"
    echo "Building aurproxy for Target: $VERSION ($OUT)"
    echo "--------------------------------------------------"
    
    # Run from project root (assumed to be current directory)
    docker build --platform linux/amd64 -t "$TAG" -f "$DOCKERFILE" .
    docker run --rm --platform linux/amd64 -v "$(pwd):/dist" "$TAG"
    
    # Ensure file is correctly named
    if [ -f "$SRC_OUT" ]; then
        mv "$SRC_OUT" "$OUT"
    fi
    chmod +x "$OUT"
    echo "Done! $OUT has been created."
}

# Check arguments
if [ -z "$1" ]; then
    usage
fi

TARGET=$1

if [ "$TARGET" == "all" ]; then
    build_target 7
    build_target 8
    build_target 9
else
    case $TARGET in
        7|8|9)
            build_target "$TARGET"
            ;;
        *)
            usage
            ;;
    esac
fi
