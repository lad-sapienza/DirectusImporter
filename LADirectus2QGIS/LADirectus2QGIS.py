import importlib
import sys
import os
import json
import time
import requests

from osgeo import ogr  # for GeoJSON to WKT conversion

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QVariant, QSettings
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsWkbTypes,
)

from .settings_dialog import SettingsDialog


def geojson_to_wkt(geojson_dict):
    try:
        geom = ogr.CreateGeometryFromJson(json.dumps(geojson_dict))
        if geom is not None:
            return geom.ExportToWkt()
    except Exception as e:
        print(f"Error converting GeoJSON to WKT: {e}")
    return None


class LADirectus2QGIS:
    def __init__(self, iface):
        self.debug_mode = True  # Set to False to hide Reload Plugin in production
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.cache_path = os.path.join(self.plugin_dir, ".directus_cache.json")
        self.cache_timeout_seconds = 3600  # 1 hour

        self.settings = QSettings()
        self.instance_url = self.settings.value("LADirectus2QGIS/instance_url", "")
        self.collection = self.settings.value("LADirectus2QGIS/collection", "")
        self.token = self.settings.value("LADirectus2QGIS/token", "")
        self.geom_field = self.settings.value("LADirectus2QGIS/geom_field", "geometry")
        self.selected_fields_json = self.settings.value("LADirectus2QGIS/selected_fields", "[]")

    def initGui(self):
        self.import_action = QAction("Import from Directus", self.iface.mainWindow())
        self.settings_action = QAction("Settings", self.iface.mainWindow())

        self.import_action.triggered.connect(self.run)
        self.settings_action.triggered.connect(self.open_settings)

        self.iface.addPluginToMenu("&LADirectus2QGIS", self.import_action)
        self.iface.addPluginToMenu("&LADirectus2QGIS", self.settings_action)

        if self.debug_mode:
            self.reload_action = QAction("Reload LADirectus2QGIS", self.iface.mainWindow())
            self.reload_action.triggered.connect(self.reload_plugin)
            self.iface.addPluginToMenu("&LADirectus2QGIS", self.reload_action)

    def unload(self):
        self.iface.removePluginMenu("&LADirectus2QGIS", self.import_action)
        self.iface.removePluginMenu("&LADirectus2QGIS", self.settings_action)
        if self.debug_mode:
            self.iface.removePluginMenu("&LADirectus2QGIS", self.reload_action)

    def reload_plugin(self):
        try:
            import importlib
            import sys
            from qgis.utils import plugins, iface
            from . import LADirectus2QGIS

            plugin_name = "LADirectus2QGIS"

            print("🔁 Reloading plugin manually (QGIS 3.x method)...")

            if plugin_name in plugins:
                plugins[plugin_name].unload()
                del plugins[plugin_name]

            for name in list(sys.modules):
                if name.startswith("LADirectus2QGIS"):
                    del sys.modules[name]

            import LADirectus2QGIS
            importlib.reload(LADirectus2QGIS)

            plugin = LADirectus2QGIS.classFactory(iface)
            plugin.initGui()
            plugins[plugin_name] = plugin

            self.iface.messageBar().pushMessage(
                "Plugin Reloaded",
                f"{plugin_name} successfully reloaded.",
                level=0,
                duration=3
            )

        except Exception as e:
            self.iface.messageBar().pushCritical("Reload Error", str(e))

    def open_settings(self):
      dlg = SettingsDialog(
          self.instance_url,
          self.collection,
          self.token,
          self.selected_fields_json,
          self.geom_field
      )
      if dlg.exec_():
          self.instance_url = dlg.url_input.text()
          self.collection = dlg.collection_dropdown.currentText()
          self.token = dlg.token_input.text()
          self.geom_field = dlg.geom_field_dropdown.currentText()
          self.selected_fields_json = dlg.get_selected_fields_json()

          self.settings.setValue("LADirectus2QGIS/instance_url", self.instance_url)
          self.settings.setValue("LADirectus2QGIS/collection", self.collection)
          self.settings.setValue("LADirectus2QGIS/token", self.token)
          self.settings.setValue("LADirectus2QGIS/geom_field", self.geom_field)
          self.settings.setValue("LADirectus2QGIS/selected_fields", self.selected_fields_json)

    def fetch_data(self, force_refresh=False):
      if not self.instance_url or not self.collection:
          self.iface.messageBar().pushWarning(
              "Directus Importer", "Missing API URL or collection."
          )
          return None

      selected_fields = json.loads(self.selected_fields_json)
      fields_query = f"&fields={','.join(selected_fields)}" if selected_fields else ""
      headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

      all_data = []
      limit = 100  # items per page
      offset = 0

      try:
          while True:
              url = f"{self.instance_url.rstrip('/')}/items/{self.collection}?limit={limit}&offset={offset}{fields_query}"
              response = requests.get(url, headers=headers)
              response.raise_for_status()
              data = response.json()

              page_data = data.get("data", [])
              all_data.extend(page_data)

              total = data.get("meta", {}).get("pagination", {}).get("total", None)
              count = len(all_data)

              if total is not None and count >= total:
                  break
              if not page_data:
                  break

              offset += limit

          # Cache the full dataset
          with open(os.path.join(self.plugin_dir, "api_debug_dump.json"), "w", encoding="utf-8") as f:
              json.dump({"data": all_data}, f, indent=2)
          with open(self.cache_path, "w", encoding="utf-8") as f:
              json.dump({"data": all_data}, f)

          return {"data": all_data}

      except Exception as e:
          self.iface.messageBar().pushWarning(
              "Directus Importer", f"Failed to fetch data: {e}"
          )
          return None

    def get_qgis_geom_type(self, features_data, geom_field):
        for item in features_data:
            wkt = None
            raw_geom = item.get(geom_field, "")
            try:
                if isinstance(raw_geom, dict) and "type" in raw_geom and "coordinates" in raw_geom:
                    wkt = geojson_to_wkt(raw_geom)
                elif isinstance(raw_geom, list) and len(raw_geom) == 2:
                    lon = float(raw_geom[0])
                    lat = float(raw_geom[1])
                    wkt = f"POINT({lon} {lat})"
                elif isinstance(raw_geom, str):
                    wkt = raw_geom
            except Exception:
                continue
            if wkt:
                try:
                    geom = QgsGeometry.fromWkt(wkt)
                    if geom and geom.isGeosValid():
                        wkb_type = geom.wkbType()
                        qgis_geom_type = QgsWkbTypes.displayString(wkb_type)
                        valid_types = {
                            "Point",
                            "MultiPoint",
                            "LineString",
                            "MultiLineString",
                            "Polygon",
                            "MultiPolygon",
                        }
                        if qgis_geom_type in valid_types:
                            return qgis_geom_type
                except Exception:
                    continue
        return "None"

    def run(self):
        data = self.fetch_data()
        if data is None:
            return

        features_data = data.get("data", [])
        if not features_data:
            self.iface.messageBar().pushWarning(
                "Directus Importer", "No data found in collection."
            )
            return

        use_geometry = self.geom_field and self.geom_field in features_data[0]
        crs = "EPSG:4326"
        selected_fields = json.loads(self.selected_fields_json)

        geom_type = "None"
        if use_geometry:
            geom_type = self.get_qgis_geom_type(features_data, self.geom_field)

        layer_def = f"{geom_type}?crs={crs}"
        layer = QgsVectorLayer(layer_def, f"Directus: {self.collection}", "memory")
        provider = layer.dataProvider()

        # Add only selected attribute fields excluding geometry field
        for field_name in selected_fields:
            if not use_geometry or field_name != self.geom_field:
                provider.addAttributes([QgsField(field_name, QVariant.String)])
        layer.updateFields()

        print("✅ Checking geometry values...")
        print("Feature keys:", features_data[0].keys())

        features = []
        for i, item in enumerate(features_data):
            print(f"▶ Feature #{i+1}")
            feat = QgsFeature()
            attr_values = []
            for f in provider.fields():
                val = item.get(f.name(), "")
                attr_values.append(str(val) if val is not None else "")
            feat.setAttributes(attr_values)

            if use_geometry:
                raw_geom = item.get(self.geom_field, "")
                print(f"→ Raw geometry value: {raw_geom}")

                if raw_geom is None:
                    print("⚠️ Missing coordinates for feature; skipping.")
                    continue

                geom = None
                try:
                    if isinstance(raw_geom, dict) and "type" in raw_geom and "coordinates" in raw_geom:
                        wkt = geojson_to_wkt(raw_geom)
                        if wkt:
                            geom = QgsGeometry.fromWkt(wkt)
                    elif isinstance(raw_geom, list) and len(raw_geom) == 2:
                        lon = float(raw_geom[0])
                        lat = float(raw_geom[1])
                        wkt = f"POINT({lon} {lat})"
                        geom = QgsGeometry.fromWkt(wkt)
                    elif isinstance(raw_geom, str):
                        geom = QgsGeometry.fromWkt(raw_geom)
                    else:
                        print("Unsupported geometry format:", type(raw_geom))
                except Exception as e:
                    print(f"Geometry parse error: {e}")

                if geom and geom.isGeosValid():
                    print(f"Parsed geometry: {geom.asWkt()}")
                    feat.setGeometry(geom)
                else:
                    print(f"Invalid geometry skipped: {raw_geom}")

            features.append(feat)

        provider.addFeatures(features)
        layer.updateExtents()
        self.iface.messageBar().pushMessage(
            "Directus Importer", f"Imported {len(features)} features.", level=0, duration=4
        )
        QgsProject.instance().addMapLayer(layer)