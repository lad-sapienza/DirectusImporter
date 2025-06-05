import os
import zipfile

PLUGIN_FOLDER = 'LADirectus2QGIS'
OUTPUT_ZIP = f'{PLUGIN_FOLDER}.zip'

# Files and folders to exclude
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

def package_plugin():
    if not os.path.isdir(PLUGIN_FOLDER):
        print(f"❌ Folder '{PLUGIN_FOLDER}' not found.")
        return

    print(f"📦 Packaging plugin: {PLUGIN_FOLDER}")
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PLUGIN_FOLDER):
            # Remove excluded directories from walk
            dirs[:] = [d for d in dirs if should_include(os.path.join(root, d))]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(PLUGIN_FOLDER))
                if should_include(rel_path):
                    zf.write(full_path, rel_path)
    print(f"✅ Plugin packaged as {OUTPUT_ZIP}")

if __name__ == '__main__':
    package_plugin()