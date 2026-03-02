⛵ Careen

Careen is a privacy-first clipboard utility for macOS and iOS that automatically "careens" your URLs—stripping away the "barnacles" of tracking parameters, resolving hidden redirects, and bypassing paywalls.

    Verb: Careen > To tilt a ship on its side for cleaning, caulking, or repairing. 

## ✨ Features

- Deep Cleaning: Removes aggressive tracking parameters (UTM, fbclid, gclid, etc.).

- Amazon De-cluttering: Rebuilds massive Amazon links into clean, shareable /dp/ canonical URLs.

- Google Search Injection: Automatically appends udm=14 and pws=0 to Google Search links for a cleaner, non-AI result page.

- Apple News Resolution: Scrapes and resolves apple.news redirects to their original source URLs.

- Paywall Bypass: Automatically routes supported paywalled sites through archive.today mirrors.

- Workspace Protection: Smart-detection ensures that Google Docs, Sheets, and Microsoft Cloud Admin links are never scrubbed.

💻 macOS Setup (Python)

The macOS version runs as a background process that monitors your clipboard in real-time.
Requirements

    Python 3.8+

    pip install requests attrs pyobjc-framework-AppKit

Installation

    Clone this repository: git clone https://github.com/timball/careen.git

    Navigate to the directory: cd careen

    Create virtual env: virtualenv venv

    Install dependancies: pip install -r requirements.txt

    Run the script: python3 ./strip-query-params-in-mac-paste-buffer.py

📱 iOS Setup (Shortcuts)

The iOS version integrates into your Share Sheet, allowing you to clean links directly from Safari or other apps.
Installation

    - Ensure "Allow Untrusted Shortcuts" is enabled in your iOS Settings.

    - Download the Careen Shortcut
    https://www.icloud.com/shortcuts/6517cdd8e1fa4f27997fd8d48ca8d4e7

    - Add the shortcut to your library.

Usage

    Share Sheet: Tap the Share icon on any webpage and select Careen. The cleaned URL will be copied to your clipboard.

    Manual: Run the shortcut while a URL is in your clipboard to sanitize it instantly.

🛠 Configuration

Both versions use a Dictionary-based Strategy Engine. You can easily add new rules:

|Domain|Action|
|--|--|
|amazon.com	| Rebuilds path to /[host]/dp/[ASIN] |
|google.com/search |	Appends udm=14 & pws=0 |
|apple.news	| Extracts redirect from HTML source |
|search.app | Extracts redirect url |
|PAYWALL SITES |	Prepends random Memento protocol enabled mirror |

🤝 Contributing

Contributions are welcome! Whether it's adding new tracking parameters to the scrubber or new paywall sites to the bypass list, feel free to open a Pull Request.

📜 License

This project is licensed under the GPL 3.0 License - see the LICENSE file for details.
