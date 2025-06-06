import os
import zipfile
import re

PLUGIN_FOLDER = 'DirectusImporter'
VERSION = 'unknown'
OUTPUT_ZIP = None

EXCLUDE = {
    '.DS_Store',
    '__pycache__',
    '.git',
    '.gitignore',
    '.idea',
    '.vscode',
    'api_debug_dump.json',
    '.directus_cache.json',
    '*.pyc',
    '*.pyo',
    '*.swp',
}

def should_include(file_path):
    for pattern in EXCLUDE:
        if pattern.startswith('*'):
            if file_path.endswith(pattern[1:]):
                return False
        else:
            if pattern in file_path.split(os.sep):
                return False
    return True

def read_version_from_metadata():
    metadata_path = os.path.join(PLUGIN_FOLDER, 'metadata.txt')
    version_pattern = re.compile(r'^version\s*=\s*(.+)$', re.IGNORECASE)
    if not os.path.isfile(metadata_path):
        print("⚠️ metadata.txt not found, using unknown version")
        return 'unknown'
    with open(metadata_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = version_pattern.match(line.strip())
            if match:
                return match.group(1).strip()
    print("⚠️ Version not found in metadata.txt, using unknown version")
    return 'unknown'

def package_plugin():
    global VERSION, OUTPUT_ZIP
    if not os.path.isdir(PLUGIN_FOLDER):
        print(f"❌ Folder '{PLUGIN_FOLDER}' not found.")
        return

    VERSION = read_version_from_metadata()
    OUTPUT_ZIP = f"{PLUGIN_FOLDER}_{VERSION}.zip"
    output_path = os.path.join(os.getcwd(), OUTPUT_ZIP)

    print(f"📦 Packaging plugin: {PLUGIN_FOLDER} (version {VERSION})")
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PLUGIN_FOLDER):
            dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(PLUGIN_FOLDER))
                if should_include(rel_path):
                    zf.write(full_path, rel_path)
    print(f"✅ Plugin packaged as {output_path}")

if __name__ == '__main__':
    package_plugin()