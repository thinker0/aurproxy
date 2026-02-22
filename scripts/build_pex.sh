#!/bin/bash
set -e
docker build --platform linux/amd64 -t aurproxy-centos7 -f Dockerfile.centos .
docker run --rm --platform linux/amd64 -v "$(pwd):/dist" aurproxy-centos7
chmod +x aurproxy-7.pex
echo "Created aurproxy.pex (CentOS 7)"
