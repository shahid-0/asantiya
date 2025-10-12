# Asantiya – Bringing Ease to Your Deployment Workflow

**Asantiya** (*Pashto: اسانتیا*) isn't just a name – it embodies the spirit of the tool. In Pashto:

- **asan (اسان)** = *easy*  
- **asantiya (اسانتیا)** = *ease*, *comfort*, *convenience*

This CLI tool makes deploying applications effortless, whether you're targeting local environments or remote servers.

[![PyPI version](https://img.shields.io/pypi/v/asantiya)](https://pypi.org/project/asantiya/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/shahid-0/asantiya/workflows/CI/badge.svg)](https://github.com/shahid-0/asantiya/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://codecov.io/gh/shahid-0/asantiya/branch/main/graph/badge.svg)](https://codecov.io/gh/shahid-0/asantiya)

## ✨ Why Asantiya?

- **🚀 Zero-Deploy-Friction**: Automate deployments so you can focus on coding, not server setup
- **🌍 Environment Agnostic**: Works seamlessly for both local testing and production environments
- **🐳 Docker-Powered**: Ensures consistency across environments with containerization
- **👨‍💻 Developer-Friendly**: Intuitive CLI commands with beautiful output and progress tracking
- **📝 Config-Driven**: Control ports, images, and environments through simple YAML files
- **🔧 Highly Configurable**: Support for multiple architectures, remote builds, and complex service dependencies
- **🛡️ Production Ready**: Comprehensive error handling, logging, and validation

## 🚀 Quick Start

```bash
# Install Asantiya
pip install asantiya

# Initialize your project
asantiya init

# Deploy your application
asantiya deploy
```

## 📖 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Commands](#commands)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### From PyPI (Recommended)

```bash
pip install asantiya
```

### From Source

```bash
git clone https://github.com/shahid-0/asantiya.git
cd asantiya
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/shahid-0/asantiya.git
cd asantiya
pip install -e ".[dev]"
```

## 🎯 Quick Start

### 1. Initialize Your Project

```bash
# Interactive setup
asantiya init

# Or use a template
asantiya init --template basic
asantiya init --template full
asantiya init --template minimal
```

### 2. Configure Your Application

Asantiya will create a `deploy.yaml` file with your configuration:

```yaml
# Main application configuration
service: my-app
image: my-app:latest

# Server connection details (use environment variables)
server: ${SERVER}

# Port mappings (host:container)
app_ports: 8080:80

# Build configuration
builder:
  arch: amd64
  local: true

# Container services definitions
accessories:
  db:
    service: my-app-db
    image: postgres:13
    ports: 5432:5432
    env:
      POSTGRES_PASSWORD: "secure-password"
    volumes:
      - db_data:/var/lib/postgresql/data
    network: my-app-network
```

### 3. Deploy Your Application

```bash
# Deploy with confirmation
asantiya deploy

# Deploy without confirmation
asantiya deploy --force

# Deploy with custom config
asantiya deploy --config production.yaml
```

## ⚙️ Configuration

### Configuration File Structure

The `deploy.yaml` file supports the following structure:

```yaml
# Required fields
service: string              # Application service name
image: string               # Docker image name
app_ports: string           # Port mapping (host:container)

# Optional fields
server: string              # Server hostname/IP
environment:                # Environment variables
  KEY: value
volumes:                    # Volume mounts
  - host_path:container_path
network: string             # Docker network name

# Build configuration
builder:
  arch: amd64|arm64|armv7  # Target architecture
  local: boolean           # Local or remote build
  remote: string           # Remote Docker URL (if not local)
  dockerfile: string       # Dockerfile path
  build_args:              # Build arguments
    KEY: value

# Accessory services
accessories:
  service_name:
    service: string         # Container name
    image: string          # Docker image
    ports: string          # Port mapping
    env:                   # Environment variables
      KEY: value
    volumes:               # Volume mounts
      - host_path:container_path
    network: string        # Docker network
    depends_on:            # Service dependencies
      - other_service
    options:               # Container options
      restart: always|unless-stopped|on-failure|no
```

### Environment Variables

Asantiya supports environment variable substitution in configuration files:

```yaml
service: ${APP_NAME}
image: ${DOCKER_REGISTRY}/${APP_NAME}:${VERSION}
server: ${DEPLOY_SERVER}
```

Required environment variables can be specified:

```bash
asantiya deploy --required-vars SERVER,APP_NAME,VERSION
```

## 📋 Commands

### Main Commands

| Command | Description |
|---------|-------------|
| `asantiya init` | Initialize configuration files |
| `asantiya deploy` | Build and deploy application |
| `asantiya app` | Manage main application container |
| `asantiya accessory` | Manage accessory containers |

### Application Management

```bash
# Start application
asantiya app start

# Stop application
asantiya app stop

# Restart application
asantiya app restart

# Remove application
asantiya app remove
```

### Accessory Management

```bash
# Start all accessories
asantiya accessory up

# Stop all accessories
asantiya accessory down

# List accessories
asantiya accessory ls

# View logs
asantiya accessory logs db

# Restart specific accessory
asantiya accessory restart db

# Reboot accessory (stop, remove, recreate)
asantiya accessory reboot db
```

### Deployment Options

```bash
# Deploy with options
asantiya deploy --force --skip-build --skip-accessories

# Use custom configuration
asantiya deploy --config production.yaml

# Enable verbose output
asantiya deploy --verbose
```

## 💡 Examples

### Basic Web Application

```yaml
service: webapp
image: webapp:latest
app_ports: 8080:80
builder:
  arch: amd64
  local: true
accessories:
  db:
    service: webapp-db
    image: postgres:13
    ports: 5432:5432
    env:
      POSTGRES_DB: webapp
      POSTGRES_PASSWORD: secure-password
    volumes:
      - db_data:/var/lib/postgresql/data
    network: webapp-network
```

### Microservices with Dependencies

```yaml
service: api-gateway
image: api-gateway:latest
app_ports: 8080:80
builder:
  arch: amd64
  local: false
  remote: ssh://build@ci.example.com
accessories:
  auth-service:
    service: auth-service
    image: auth-service:latest
    ports: 3001:3000
    network: microservices-network
    depends_on: [redis, postgres]
  
  redis:
    service: redis
    image: redis:alpine
    ports: 6379:6379
    network: microservices-network
  
  postgres:
    service: postgres
    image: postgres:13
    ports: 5432:5432
    env:
      POSTGRES_PASSWORD: secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    network: microservices-network
```

### Multi-Architecture Build

```yaml
service: multiarch-app
image: multiarch-app:latest
app_ports: 8080:80
builder:
  arch: arm64
  local: false
  remote: ssh://build@arm-server.com
  build_args:
    BUILD_ENV: production
```

## 🧪 Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/shahid-0/asantiya.git
cd asantiya

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
flake8 asantiya tests
black asantiya tests
isort asantiya tests

# Type checking
mypy asantiya
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=asantiya --cov-report=html

# Run specific test file
pytest tests/test_schemas.py

# Run with verbose output
pytest -v
```

### Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **pre-commit**: Git hooks

### Project Structure

```
asantiya/
├── asantiya/                 # Main package
│   ├── accessories/          # Accessory management commands
│   ├── app/                  # Application management commands
│   ├── schemas/              # Pydantic models
│   ├── utils/                # Utility functions
│   ├── cli.py               # Main CLI interface
│   ├── deploy.py            # Deployment commands
│   ├── docker_manager.py    # Docker operations
│   ├── init.py              # Initialization commands
│   └── logger.py            # Logging configuration
├── tests/                   # Test suite
├── .github/workflows/       # CI/CD pipelines
├── docs/                    # Documentation
└── examples/                # Example configurations
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Run code quality checks (`pre-commit run --all-files`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Reporting Issues

Please report bugs and request features through [GitHub Issues](https://github.com/shahid-0/asantiya/issues).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Docker](https://www.docker.com/) for containerization
- [Typer](https://typer.tiangolo.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [Paramiko](https://www.paramiko.org/) for SSH connections

## 📞 Support

- 📖 [Documentation](https://github.com/shahid-0/asantiya#readme)
- 🐛 [Report Issues](https://github.com/shahid-0/asantiya/issues)
- 💬 [Discussions](https://github.com/shahid-0/asantiya/discussions)
- 📧 [Email](mailto:shahiddev91@gmail.com)

---

Made with ❤️ by [Shahid Khan](https://github.com/shahid-0)