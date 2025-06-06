def classFactory(iface):
    from .DirectusImporter import DirectusImporter
    return DirectusImporter(iface)