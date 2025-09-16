# 🚀 WhisperEngine Distribution & Release Guide

## Overview
This guide covers the complete distribution pipeline for WhisperEngine native applications across macOS, Windows, and Linux.

## 📋 Release Process

### 1. **Automatic Releases (Recommended)**
```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```
This automatically triggers:
- Cross-platform builds (macOS, Windows, Linux)  
- Code signing (where configured)
- Professional installer creation
- GitHub Release with download links

### 2. **Manual Development Builds**
Go to GitHub Actions → "Build Cross-Platform Releases" → "Run workflow"
- Choose custom version or use "development"
- Builds are uploaded as workflow artifacts

### 3. **Local Testing**
```bash
# Test local build
source .venv/bin/activate
python build_cross_platform.py build --platform darwin
```

## 🔐 Code Signing Setup

### macOS Signing (Required for Distribution)
1. **Get Apple Developer Certificate**
   - Join Apple Developer Program ($99/year)
   - Create "Developer ID Application" certificate
   - Export as .p12 file

2. **Add GitHub Secrets**
   ```
   APPLE_CERTIFICATE=<base64 encoded .p12 file>
   APPLE_CERTIFICATE_PASSWORD=<certificate password>
   APPLE_SIGNING_IDENTITY=<certificate name>
   ```

3. **Generate Base64**
   ```bash
   base64 -i certificate.p12 -o certificate.txt
   ```

### Windows Signing (Optional but Recommended)
1. **Get Code Signing Certificate**
   - Purchase from DigiCert, Sectigo, etc.
   - Or use self-signed for internal distribution

2. **Add GitHub Secrets**
   ```
   WINDOWS_CERTIFICATE=<base64 encoded certificate>
   WINDOWS_CERTIFICATE_PASSWORD=<certificate password>
   ```

### Linux (No Signing Required)
Linux builds work without code signing. Users may need to mark as executable.

## 📦 Distribution Outputs

### 🍎 macOS
- **WhisperEngine.app** - Native app bundle
- **WhisperEngine-macOS-[arch]-[version].dmg** - Professional installer
- **Architectures**: arm64 (Apple Silicon), x64 (Intel)

### 🪟 Windows  
- **WhisperEngine.exe** - Standalone executable
- **WhisperEngine-Windows-[arch]-[version].zip** - Portable package
- **Architectures**: x64, x86 (32-bit)

### 🐧 Linux
- **WhisperEngine** - Native binary
- **WhisperEngine-Linux-[arch]-[version].tar.gz** - Distribution package  
- **Architectures**: x64, arm64

## 🌐 Download Locations

### Public Releases
**Primary**: https://github.com/whisperengine-ai/whisperengine/releases
- Professional download page
- Latest and historical versions
- Release notes and changelog
- Direct download links

### Development Builds
**GitHub Actions Artifacts** (Team Access Only)
- Repository → Actions → Build workflow → Artifacts
- 30-day retention
- Testing and preview builds

## 🔄 Version Management

### Semantic Versioning
```
v1.0.0 - Major release
v1.1.0 - Minor release  
v1.1.1 - Patch release
```

### Version Sources
1. **Git Tags** (Primary): `git tag v1.2.0`
2. **Manual Input**: Workflow dispatch custom version
3. **Auto-generated**: Development builds use commit hash

## 📋 Pre-Release Checklist

### Before Creating Release Tag:
- [ ] All tests pass locally
- [ ] UI changes tested on target platforms
- [ ] Dependencies updated and verified
- [ ] Version number decided (semantic versioning)
- [ ] Release notes prepared
- [ ] Code signing certificates valid

### Deployment Steps:
1. **Merge** feature branch to main
2. **Test** final build locally
3. **Tag** release: `git tag v1.0.0`  
4. **Push** tag: `git push origin v1.0.0`
5. **Monitor** GitHub Actions build
6. **Verify** release artifacts
7. **Test** downloads on each platform

## 🛠️ Troubleshooting

### Build Failures
- Check GitHub Actions logs
- Verify dependencies in requirements.txt
- Test local build first

### Signing Issues
- Verify certificate expiration
- Check GitHub secrets configuration
- Test certificate locally

### Distribution Problems
- Verify file permissions (Linux)
- Check antivirus false positives (Windows)
- Test installer on clean systems

## 📈 Analytics & Downloads

### GitHub Release Metrics
- Download counts per release
- Platform popularity analytics
- Release engagement tracking

### Monitoring
- GitHub Actions build success rates
- User feedback on installation issues
- Platform-specific bug reports

## 🎯 Future Enhancements

### Professional Installers
- **macOS**: Notarization for Gatekeeper bypass
- **Windows**: MSI installer with Windows Installer
- **Linux**: .deb/.rpm packages for package managers

### Auto-Updates
- Built-in update mechanism
- Delta updates for smaller downloads
- Rollback capability

### Enterprise Distribution
- Private repository support
- Enterprise certificate management
- Bulk deployment tools

---

## 🚀 Quick Start Command

```bash
# Create your first release
git tag v1.0.0-beta
git push origin v1.0.0-beta
```

The GitHub Actions workflow will handle the rest automatically! ✨