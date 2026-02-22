#!/bin/bash
set -e
docker build --platform linux/amd64 -t aurproxy-rocky9 -f Dockerfile.rocky9 .
docker run --rm --platform linux/amd64 -v "$(pwd):/dist" aurproxy-rocky9
chmod +x aurproxy-9.pex
echo "Created aurproxy-9.pex"
