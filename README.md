# 🎵 Album Scanner

A desktop application that scans your local music collection for incomplete albums and fetches missing track information from Spotify. Organize your music library effortlessly!

![Album Scanner](https://img.shields.io/badge/Python-3.8+-blue.svg)

---

## 📋 Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output Format](#output-format)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Automatic Scanning** | Walks through your music folders recursively |
| 🎵 **Metadata Extraction** | Reads audio file tags using Mutagen library |
| 🎧 **Spotify Integration** | Fetches missing track info from Spotify API |
| 🔒 **Secure Credentials** | Fernet encryption for local credential storage |
| 💻 **Tkinter GUI** | Clean desktop interface with status updates |
| 📄 **Result Export** | Saves detailed scan results to timestamped text files |
| ⚙️ **Configurable** | Set minimum track threshold to skip singles/EPs |

---

## 🛠️ Prerequisites

### Spotify Developer Account (Optional)

- Required for Spotify API integration
- Create at [Spotify for Developers](https://developer.spotify.com/dashboard)
- Generate Client ID and Secret credentials

---

## 📦 Installation

1. **Clone or download** this script:
   ```bash
   git clone https://WhyTryNow/AlbumScanner
   cd AlbumScanner
   ```
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate # On Mac: source .venv/bin/activate
   ```
3. **Install Python dependencies**:
   ```bash
   pip install mutagen spotipy cryptography
   ```
---

## ⚙️ Configuration

### Spotify API Setup

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app to get your Client ID and Secret
3. Save credentials securely using the built-in manager:

```python
# Example credential file structure (encrypted):
{"client_id": "your_spotify_client_id", "client_secret": "your_secret"}
```

### Default Settings

| Setting | Default Value | Description |
|---------|--------------|-------------|
| Minimum Tracks | 3 | Albums with fewer tracks are skipped (singles/EPs) |
| Supported Formats | .flac, .mp3, .m4a, .wav | Audio files scanned for metadata |
| Results File | `scan_results_YYYYMMDD_HHMMSS.txt` | Timestamped output filename |

---

## 🎯 Usage

### Quick Start Guide

# 1. Run the application
```bash
python AlbumScanner.py
```

# 2. Configure settings in the GUI:
   - Enter Spotify Client ID (optional)
   - Enter Spotify Client Secret (optional)
   - Set minimum track threshold
   - Browse and select your music folder

# 3. Click "Browse" to select a music directory

# 4. Click "Scan Albums" to begin scanning


### GUI Workflow

1. **Enter Spotify Credentials** (recommended for full functionality)
2. **Click Save Credentials** to encrypt and store locally
3. **Select Music Folder** using the Browse button
4. **Adjust Minimum Tracks** threshold if needed
5. **Click Scan Albums** to begin scanning

### Command Line Alternative (for automation)

```bash
# Run with specific parameters
python Album Scanner.py --folder "/path/to/music" --min-tracks 3
```

---

## 📊 Output Format

Scan results are saved to a timestamped text file:

```
📊 Album Scan Results
==================================================

🎤 Artist Name
----------------------------------------

   💿 Album: Album Name
   📀 Total Tracks: 15
   ✅ Present: 8 | ❌ Missing: 7
   🚫 Missing Tracks: Song A, Song B, Track 3, ...
   🔗 Spotify URL: https://open.spotify.com/album/XXXXX

... more albums ...
```

---

## 🔒 Security Notes

### Credential Encryption

- All Spotify credentials are encrypted using Fernet symmetric encryption
- Key file: `scanner_key.key` (auto-generated on first run)
- Credentials file: `credentials.enc` (encrypted storage)

### Best Practices

| ✅ Recommended | ⚠️ Caution | ❌ Avoid |
|---------------|------------|----------|
| Store credentials locally encrypted | Use HTTPS connections | Commit credentials to Git |
| Regularly rotate Spotify API keys | Share unencrypted files | Run on public/shared computers |
| Keep Python dependencies updated | Download from trusted sources only | Expose scanner to untrusted networks |

---

## 🐛 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Spotify Failed" error | Check Spotify Developer Dashboard credentials are correct |
| "Folder not found" error | Verify the music folder path exists and is accessible |
| No tracks detected | Ensure audio files have proper metadata tags (ID3, Vorbis, etc.) |
| "Permission denied" | Run the script with appropriate file permissions |
| Slow scanning on large folders | Scanning is recursive; patience advised for large collections |

### Debug Mode

Add this to see detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📁 File Structure

```
AlbumScanner/
├── Album Scanner.py          # Main application
├── scanner_key.key           # Encryption key (auto-generated)
├── credentials.enc           # Encrypted credentials
├── scan_results_*.txt        # Generated 
```

---

## 📄 License

This project is provided as-is for personal use. Please respect:

- Spotify's Terms of Service and API usage policies
- Local file system privacy considerations
- User data security best practices

---

## 🤝 Contributing

To report issues or request features:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)

---

## 📞 Support

For assistance with:

- Spotify API integration issues
- Metadata extraction problems
- Cryptographic key management

Please create an issue or contact the maintainer directly.

---

**Built with Python • Powered by Spotify API • Secure by Default** 🎵

