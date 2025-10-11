# 🌐 WhisperEngine Cross-Platform Docker Compatibility

## ✅ Supported Platforms

WhisperEngine Docker containers work seamlessly across all major platforms:

### macOS
- **Intel Macs**: Full support with `linux/amd64` images
- **Apple Silicon (M1/M2/M3)**: Full support with `linux/arm64` images
- **Docker Desktop**: Recommended installation method
- **Performance**: Native ARM64 performance on Apple Silicon

### Linux
- **x86_64**: Full support with `linux/amd64` images
- **ARM64/aarch64**: Full support with `linux/arm64` images (Raspberry Pi, ARM servers)
- **Distribution**: Works on Ubuntu, Debian, CentOS, Fedora, Arch, etc.
- **Docker Engine**: Direct installation or Docker Desktop

### Windows
- **WSL2 + Docker Desktop**: Recommended setup (full compatibility)
- **Docker Desktop with Hyper-V**: Also supported
- **x86_64**: Full support with `linux/amd64` images
- **Performance**: WSL2 provides near-native Linux performance

## 🔧 Multi-Architecture Build Strategy

### GitHub Actions Workflow
Our automated builds create multi-platform images:

```yaml
platforms: linux/amd64,linux/arm64
```

### Docker Hub Images
- **whisperengine/whisperengine:latest** - Multi-arch manifest
- **whisperengine/whisperengine:linux-amd64** - Intel/AMD specific
- **whisperengine/whisperengine:linux-arm64** - ARM specific

### Automatic Selection
Docker automatically pulls the correct architecture:
```bash
# Automatically selects linux/amd64 on Intel/AMD systems
# Automatically selects linux/arm64 on ARM systems (M1 Mac, Raspberry Pi)
docker pull whisperengine/whisperengine:latest
```

## 🏗️ Infrastructure Compatibility

### Database Images
All infrastructure uses multi-arch images:

- **PostgreSQL**: `postgres:16-alpine` (amd64, arm64)
- **Qdrant**: `qdrant/qdrant:v1.8.1` (amd64, arm64)

### Volume Strategies
Both volume strategies work cross-platform:

#### Docker Named Volumes (Default)
```bash
# Works identically on all platforms
volumes:
  - postgres_data:/var/lib/postgresql/data
```

#### Host Filesystem Mounts
```bash
# Platform-specific paths but same Docker Compose syntax
# macOS/Linux: ./data/postgres:/var/lib/postgresql/data
# Windows WSL2: ./data/postgres:/var/lib/postgresql/data
```

## 🚀 Platform-Specific Setup

### macOS Setup
```bash
# Install Docker Desktop from docker.com
# Clone and run (no additional steps needed)
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine/docker/quick-start
cp .env.minimal .env
# Edit .env with your settings
docker-compose up -d
```

### Linux Setup
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in

# Clone and run
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine/docker/quick-start
cp .env.minimal .env
# Edit .env with your settings
docker-compose up -d
```

### Windows Setup
```bash
# Install WSL2 + Docker Desktop
# In WSL2 terminal:
git clone https://github.com/whisperengine-ai/whisperengine.git
cd whisperengine/docker/quick-start
cp .env.minimal .env
# Edit .env with your settings
docker-compose up -d
```

## 🔍 Verification Commands

### Check Architecture
```bash
# Verify your platform
docker version --format '{{.Server.Arch}}'

# Check running containers
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Inspect image architecture
docker image inspect whisperengine/whisperengine:latest | grep Architecture
```

### Health Checks
```bash
# Health endpoint (works on all platforms)
curl http://localhost:9090/health

# Container logs
docker logs whisperengine-bot
docker logs whisperengine-postgres
docker logs whisperengine-qdrant
```

## 🎯 Performance Considerations

### Apple Silicon (M1/M2/M3)
- **Native ARM64**: Excellent performance with native images
- **No emulation overhead**: Direct ARM64 execution
- **Memory efficiency**: Better than x86_64 emulation

### Windows WSL2
- **Near-native performance**: WSL2 provides Linux kernel
- **File system**: Keep files in WSL2 filesystem for best performance
- **Memory allocation**: Configure WSL2 memory limits in `.wslconfig`

### Raspberry Pi / ARM Servers
- **Full support**: Native ARM64 builds available
- **Resource usage**: Configure lower memory limits for smaller systems
- **Storage**: Use fast SD cards (Class 10+) or USB 3.0 drives

## 🛡️ Security & Permissions

### Docker Daemon Access
- **macOS/Windows**: Docker Desktop handles permissions automatically
- **Linux**: Add user to docker group: `sudo usermod -aG docker $USER`

### File Permissions
- **Host mounts**: Ensure proper ownership when using filesystem mounts
- **SELinux/AppArmor**: May require additional configuration on hardened systems

## 🔧 Troubleshooting

### Common Platform Issues

#### macOS
- **Docker Desktop not starting**: Check virtualization is enabled
- **Port conflicts**: Ensure ports 5432, 6333, 6334, 9090 are available

#### Linux
- **Permission denied**: Add user to docker group and re-login
- **Systemd issues**: Ensure Docker service is running: `sudo systemctl start docker`

#### Windows
- **WSL2 not enabled**: Enable WSL2 feature in Windows Features
- **Docker Desktop WSL integration**: Enable in Docker Desktop settings

### Generic Docker Issues
```bash
# Reset containers
docker-compose down
docker-compose up -d

# Clean rebuild
docker-compose down
docker system prune -f
docker-compose pull
docker-compose up -d

# Check logs
docker-compose logs --tail=50
```

## 📚 Additional Resources

- [Docker Desktop Installation](https://docs.docker.com/desktop/)
- [WSL2 Setup Guide](https://docs.microsoft.com/en-us/windows/wsl/install)
- [Docker Engine Installation (Linux)](https://docs.docker.com/engine/install/)
- [Multi-platform builds](https://docs.docker.com/buildx/working-with-buildx/)