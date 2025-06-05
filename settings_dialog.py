from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator
import requests
import json


class SettingsDialog(QDialog):
    def __init__(self, url, collection, token, selected_fields_json, geom_field, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Directus Geo Importer Settings")

        self.url = url
        self.collection = collection
        self.token = token
        self.selected_fields = json.loads(selected_fields_json or "[]")
        self.geom_field = geom_field

        main_layout = QVBoxLayout()

        # === Instance settings group ===
        instance_group = QGroupBox("Directus Instance Settings")
        instance_layout = QVBoxLayout()

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Directus API URL:")
        self.url_input = QLineEdit(self.url)
        self.url_input.setToolTip("Base URL of your Directus instance, e.g. https://mydirectus.example.com")
        # URL validator (simple regex for http/https)
        url_regex = QRegExp(r"https?://.+")
        self.url_input.setValidator(QRegExpValidator(url_regex, self))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        instance_layout.addLayout(url_layout)

        # Token input
        token_layout = QHBoxLayout()
        token_label = QLabel("Auth Token:")
        self.token_input = QLineEdit(self.token)
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setToolTip("Your Directus API authentication token")
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        instance_layout.addLayout(token_layout)

        # Collection dropdown
        collection_layout = QHBoxLayout()
        collection_label = QLabel("Collection:")
        self.collection_dropdown = QComboBox()
        self.collection_dropdown.setToolTip("Select the collection/table to import from")
        collection_layout.addWidget(collection_label)
        collection_layout.addWidget(self.collection_dropdown)
        instance_layout.addLayout(collection_layout)

        # Load collections button and status label
        load_coll_layout = QHBoxLayout()
        self.btn_refresh_collections = QPushButton("Load Collections")
        self.btn_refresh_collections.setToolTip("Load available collections from the Directus instance")
        load_coll_layout.addWidget(self.btn_refresh_collections)
        self.coll_status_label = QLabel("")
        load_coll_layout.addWidget(self.coll_status_label)
        instance_layout.addLayout(load_coll_layout)

        instance_group.setLayout(instance_layout)
        main_layout.addWidget(instance_group)

        # === Geometry and fields group ===
        geom_fields_group = QGroupBox("Geometry & Fields Selection")
        geom_fields_layout = QVBoxLayout()

        # Geometry field dropdown
        geom_field_layout = QHBoxLayout()
        geom_field_label = QLabel("Geometry Field:")
        self.geom_field_dropdown = QComboBox()
        self.geom_field_dropdown.setToolTip("Select the field containing geometry data")
        geom_field_layout.addWidget(geom_field_label)
        geom_field_layout.addWidget(self.geom_field_dropdown)
        geom_fields_layout.addLayout(geom_field_layout)

        # Fields checklist label
        geom_fields_layout.addWidget(QLabel("Select fields to import:"))

        # Fields checklist
        self.fields_list = QListWidget()
        geom_fields_layout.addWidget(self.fields_list)

        # Load fields button and status label
        load_fields_layout = QHBoxLayout()
        self.btn_refresh_fields = QPushButton("Load Fields")
        self.btn_refresh_fields.setToolTip("Load available fields from the selected collection")
        load_fields_layout.addWidget(self.btn_refresh_fields)
        self.fields_status_label = QLabel("")
        load_fields_layout.addWidget(self.fields_status_label)
        geom_fields_layout.addLayout(load_fields_layout)

        geom_fields_group.setLayout(geom_fields_layout)
        main_layout.addWidget(geom_fields_group)

        # OK and Cancel buttons
        buttons_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.setDefault(True)
        btn_cancel = QPushButton("Cancel")
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Connect signals
        self.btn_refresh_collections.clicked.connect(self.load_collections)
        self.btn_refresh_fields.clicked.connect(self.load_fields)
        self.collection_dropdown.currentTextChanged.connect(self.load_fields)
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        self.url_input.textChanged.connect(self.validate_inputs)
        self.collection_dropdown.currentTextChanged.connect(self.validate_inputs)

        # Initial population
        if self.url:
            self.load_collections()
        if self.collection:
            idx = self.collection_dropdown.findText(self.collection)
            if idx >= 0:
                self.collection_dropdown.setCurrentIndex(idx)
                self.load_fields()

        self.validate_inputs()

    def validate_inputs(self):
        # Enable "Load Fields" only if URL and Collection valid
        url_valid = self.url_input.hasAcceptableInput()
        collection_selected = bool(self.collection_dropdown.currentText())
        self.btn_refresh_fields.setEnabled(url_valid and collection_selected)

    def load_collections(self):
        self.collection_dropdown.clear()
        self.coll_status_label.setText("Loading collections...")
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        if not url:
            self.coll_status_label.setText("Please enter a valid URL.")
            return
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            resp = requests.get(f"{url.rstrip('/')}/collections", headers=headers, timeout=10)
            resp.raise_for_status()
            collections = resp.json().get('data', [])
            # Filter out system tables starting with 'directus_'
            user_collections = [c for c in collections if not c['collection'].startswith('directus_')]
            for c in user_collections:
                self.collection_dropdown.addItem(c['collection'])
            self.coll_status_label.setText(f"Loaded {len(user_collections)} collections")
        except Exception as e:
            self.coll_status_label.setText(f"Failed to load collections")
            print(f"Failed to load collections: {e}")

    def load_fields(self):
        self.fields_list.clear()
        self.geom_field_dropdown.clear()
        self.fields_status_label.setText("Loading fields...")
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        collection = self.collection_dropdown.currentText()
        if not url or not collection:
            self.fields_status_label.setText("Set URL and select a collection")
            return
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            resp = requests.get(f"{url.rstrip('/')}/fields/{collection}", headers=headers, timeout=10)
            resp.raise_for_status()
            fields = resp.json().get('data', [])

            # Populate fields checklist
            for f in fields:
                field_name = f['field']
                item = QListWidgetItem(field_name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                if field_name in self.selected_fields or not self.selected_fields:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
                self.fields_list.addItem(item)

            # Populate geometry field dropdown
            for f in fields:
                self.geom_field_dropdown.addItem(f['field'])
            # Select previous geometry field if exists
            idx = self.geom_field_dropdown.findText(self.geom_field)
            if idx >= 0:
                self.geom_field_dropdown.setCurrentIndex(idx)
            self.fields_status_label.setText(f"Loaded {len(fields)} fields")

        except Exception as e:
            self.fields_status_label.setText("Failed to load fields")
            print(f"Failed to load fields: {e}")

    def get_selected_fields_json(self):
        selected = []
        for i in range(self.fields_list.count()):
            item = self.fields_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return json.dumps(selected)