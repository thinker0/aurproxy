#!/bin/bash
set -e
docker build --platform linux/amd64 -t aurproxy-rocky8 -f Dockerfile.rocky8 .
docker run --rm --platform linux/amd64 -v "$(pwd):/dist" aurproxy-rocky8
chmod +x aurproxy-8.pex
echo "Created aurproxy-8.pex"
