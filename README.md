# DirectusImporter

**Fetch geospatial and text data from a Directus API into QGIS**


## Table of Contents

- [Overview](#overview)  
- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Requirements](#requirements)  
- [Development & Debugging](#development--debugging)  
- [Contributing](#contributing)  
- [License](#license)  
- [Author](#author)  

---

## Overview

DirectusImporter is a QGIS plugin designed to seamlessly import spatial and non-spatial data from a Directus headless CMS instance into QGIS. It supports geometry field detection, selective field import, data caching, and plugin reload functionality to enhance your GIS workflows.

---

## Features

- Connect to any Directus API endpoint with optional authentication token  
- Browse and select collections (tables) from your Directus instance  
- Choose geometry field to import spatial data  
- Select which attribute fields to import via a convenient checklist  
- Pagination handling to retrieve all records from Directus  
- Caches API data locally to improve performance  
- Debug mode with plugin reload option for easy development/testing

---

## Installation

1. Download the latest release ZIP file from the [GitHub repository](https://github.com/lad-sapienza/DirectusImporter/releases).  
2. In QGIS, go to **Plugins > Manage and Install Plugins > Install from ZIP**.  
3. Select the downloaded ZIP and install.  
4. Enable the plugin via the Plugins panel.

---

## Usage

1. Open QGIS and click **Plugins > DirectusImporter > Settings**.  
2. Enter your Directus API URL and authentication token (if required).  
3. Click **Load Collections** to fetch available tables.  
4. Select the collection to import.  
5. Click **Load Fields** to fetch and display available fields.  
6. Choose the geometry field and select desired attribute fields.  
7. Click **OK** to save settings.  
8. Click **Import from Directus** from the plugin menu to load data into QGIS.

---

## Requirements

- QGIS 3.10 or higher  
- Python packages: `requests`, `osgeo` (GDAL/OGR bindings)  
- A running Directus instance with accessible API  

---

## Development & Debugging

- Enable **Debug Mode** in the plugin code to show plugin reload option.  
- Plugin caches API responses locally to `.directus_cache.json` for faster reloads.  
- Debug output is printed to QGIS Python Console.

---

## Contributing

Contributions and bug reports are welcome! Please open issues or pull requests on the [GitHub repo](https://github.com/lad-sapienza/DirectusImporter).

---

## License

GNU GPL 3 — see [LICENSE](LICENSE) file.

---

## Authors

- Julian Bogdani — julian.bogdani@uniroma1.it
- OpenAI's ChatGPT — https://chatgpt.com/

---
