# 🏗️ WhisperEngine Build System

WhisperEngine supports automated building of native executable applications for macOS, Windows, and Linux, just like Docker containers but for desktop distribution.

## 📦 What Gets Built

### 🍎 macOS
- **WhisperEngine.app** - Native application bundle
- **WhisperEngine.dmg** - Disk image installer
- **Architectures**: Intel (x64) + Apple Silicon (arm64)

### 🪟 Windows  
- **WhisperEngine.exe** - Native executable
- **WhisperEngine.zip** - Portable distribution
- **Architectures**: 64-bit (x64) + 32-bit (x86)

### 🐧 Linux
- **WhisperEngine** - Native executable
- **WhisperEngine.tar.gz** - Compressed archive
- **Architectures**: x64 + arm64

## 🚀 Automated Building (GitHub Actions)

### Trigger Builds

**Option 1: Version Tag (Recommended)**
```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# This automatically builds all platforms and creates a GitHub release
```

**Option 2: Manual Trigger**
1. Go to GitHub Actions
2. Select "Build Cross-Platform Releases"
3. Click "Run workflow"
4. Optionally specify a version

**Option 3: Pull Request**
- Builds automatically on PRs (for testing)
- No release created, just artifacts

### Build Matrix

The automation builds for **all combinations**:

| Platform | Architectures | Output Formats |
|----------|---------------|----------------|
| macOS    | x64, arm64   | .app, .dmg, .zip |
| Windows  | x64, x86     | .exe, .zip |
| Linux    | x64, arm64   | binary, .tar.gz |

### Results

**Successful builds create:**
- ✅ **GitHub Release** with all artifacts
- ✅ **Cross-platform downloads** ready for distribution
- ✅ **Signed applications** (if certificates configured)

## 🔧 Local Building & Testing

### Quick Test
```bash
# Test build for your current platform
./test_build_local.sh
```

### Manual Building
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Build for current platform
python build_cross_platform.py build

# Build for specific platform
python build_cross_platform.py build --platform darwin   # macOS
python build_cross_platform.py build --platform windows  # Windows  
python build_cross_platform.py build --platform linux    # Linux

# Build all platforms (if supported)
python build_cross_platform.py build-all
```

### Build Output
```
dist/
├── WhisperEngine.app/     # macOS
├── WhisperEngine.exe      # Windows
├── WhisperEngine          # Linux
└── [platform packages]   # .dmg, .zip, .tar.gz
```

## ⚙️ Build Configuration

### Dependencies
- **PyInstaller** - Creates single-file executables
- **Platform-specific tools** - For signing and packaging
- **UPX** - Optional compression (installed automatically)

### Platform Requirements

**macOS Building:**
- macOS 10.15+ for building
- Xcode Command Line Tools
- Optional: Apple Developer certificates for signing

**Windows Building:**
- Windows 10+ or Windows Server
- Visual Studio Build Tools (auto-installed)
- Optional: Code signing certificates

**Linux Building:**
- Ubuntu 18.04+ or equivalent
- Build tools: `gcc`, `pkg-config`
- GUI libraries: `libgtk-3-dev`, `libdbus-1-dev`

### Cross-Compilation Notes

- **Best practice**: Build on native platform for that target
- **Cross-compilation**: Limited support, may produce platform-specific builds that aren't fully native
- **GitHub Actions**: Uses native runners for each platform automatically

## 🔐 Code Signing (Optional)

### Setup Certificates

**macOS (Apple Developer Account):**
```bash
# Add these secrets to GitHub repository:
APPLE_CERTIFICATE              # Base64-encoded .p12 file
APPLE_CERTIFICATE_PASSWORD     # Certificate password
APPLE_SIGNING_IDENTITY         # Certificate identity
```

**Windows (Code Signing Certificate):**
```bash
# Add these secrets to GitHub repository:
WINDOWS_CERTIFICATE            # Base64-encoded certificate
WINDOWS_CERTIFICATE_PASSWORD   # Certificate password
```

### Benefits of Signing
- ✅ **No security warnings** when users run the app
- ✅ **Better user trust** and professional appearance
- ✅ **Required for notarization** (macOS) and distribution

## 📋 Build Process Details

### What Happens During Build

1. **Environment Setup**
   - Python environment activation
   - Dependency installation
   - Platform-specific tool setup

2. **Source Preparation** 
   - Clean previous builds
   - Generate platform-specific .spec files
   - Include UI assets, templates, static files

3. **PyInstaller Execution**
   - Analyze dependencies
   - Bundle Python interpreter
   - Create single executable
   - Apply compression (UPX)

4. **Post-Processing**
   - Code signing (if configured)
   - Package creation (.dmg, .zip, .tar.gz)
   - Artifact organization

5. **Distribution**
   - Upload to GitHub releases
   - Generate download links
   - Create release notes

### Build Time Estimates

| Platform | Architecture | Typical Build Time |
|----------|-------------|--------------------|
| macOS    | x64/arm64   | 8-12 minutes |
| Windows  | x64/x86     | 6-10 minutes |
| Linux    | x64/arm64   | 5-8 minutes |

**Total pipeline time: ~15-20 minutes** for all platforms

## 🐛 Troubleshooting

### Common Issues

**Build Fails - Missing Dependencies:**
```bash
# Install missing Python packages
pip install -r requirements.txt
pip install pyinstaller

# Platform-specific packages
pip install pyobjc-framework-Cocoa  # macOS
pip install pywin32                 # Windows
```

**Build Succeeds But App Won't Run:**
```bash
# Check for missing system libraries
ldd dist/WhisperEngine              # Linux
otool -L dist/WhisperEngine.app     # macOS

# Test in clean environment
docker run -it ubuntu:20.04        # Linux testing
```

**Large File Sizes:**
```bash
# Enable UPX compression
pip install upx-ucl

# Exclude unnecessary packages in .spec files
excludes=['tkinter', 'matplotlib', 'numpy']
```

### Debug Build Issues

**Local Debugging:**
```bash
# Run with verbose output
python build_cross_platform.py build --platform darwin 2>&1 | tee build.log

# Check PyInstaller warnings
pyinstaller --log-level DEBUG whisperengine-macos.spec
```

**GitHub Actions Debugging:**
1. Check the Actions tab for detailed logs
2. Download failed build artifacts
3. Enable debug logging in workflow

## 🔄 CI/CD Integration

### Workflow File
The build automation is defined in:
```
.github/workflows/build-releases.yml
```

### Customization
You can customize:
- **Target platforms** - Enable/disable specific OS builds
- **Architectures** - Add/remove architecture support
- **Package formats** - Add installers, AppImages, etc.
- **Signing configuration** - Add certificate management
- **Release notes** - Customize release documentation

### Status Badges
Add to your README:
```markdown
[![Build Status](https://github.com/whisperengine-ai/whisperengine/workflows/Build%20Cross-Platform%20Releases/badge.svg)](https://github.com/whisperengine-ai/whisperengine/actions)
```

## 🎯 Distribution

### End User Experience

**macOS Users:**
1. Download `.dmg` file
2. Drag app to Applications
3. Launch like any native app

**Windows Users:**
1. Download `.zip` file  
2. Extract and run `.exe`
3. No installation required

**Linux Users:**
1. Download `.tar.gz` file
2. Extract and run binary
3. Works on most distributions

### Comparison with Docker

| Aspect | Native Apps | Docker |
|--------|-------------|--------|
| **User Experience** | One-click install | Command-line setup |
| **System Integration** | Full desktop integration | Isolated environment |
| **Resource Usage** | Native performance | Container overhead |
| **Distribution** | Direct download | Registry required |
| **Updates** | App-specific updaters | Image pulls |

Both approaches are supported - use native apps for desktop users and Docker for server deployments!