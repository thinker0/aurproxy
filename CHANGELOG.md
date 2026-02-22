# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-06

### Added
- **Unified Build System**: Introduced standardized PEX build scripts supporting multiple OS targets:
  - CentOS 7 (aurproxy-7.pex)
  - Rocky Linux 8 (aurproxy-8.pex)
  - Rocky Linux 9 (aurproxy-9.pex)
- **Mac Native Testing**: Added support for building and testing with Mac-native PEX (aurproxy_mac.pex) in scripts/test_local_nginx.sh.
- **Resource Management**: Implemented reference counting for Zookeeper connections to ensure proper cleanup.
- **Performance Optimization**: Added Jinja2 template caching in Nginx backend to reduce CPU/Memory churn.

### Changed
- **Python 3 Migration**: Fully modernized the codebase to support Python 3.8, 3.9, and 3.11. Removed legacy Python 2 idioms.
- **AWS SDK Upgrade**: Replaced the deprecated boto library with modern boto3 for ELB and Route53 integrations.
- **Testing Framework**: Migrated test suite from nosetests to pytest.
- **Project Structure**: Organized Dockerfiles and build scripts into a dedicated scripts/ directory.
- **Dependency Optimization**: Standardized and pinned core dependencies in requirements.txt.

### Fixed
- **Security Vulnerabilities**: Upgraded flask, requests, jinja2, and gevent to secure versions to address multiple high-severity CVEs (RCE, credential leakage).
- **Memory Leaks**: Fixed potential memory leaks in Zookeeper Watchers and MetricStore.
- **Bug Fixes**: Resolved IndentationError in serverset.py and various ImportError issues across modules.
- **Portability**: Replaced hardcoded absolute paths with dynamic relative paths in the test suite.
