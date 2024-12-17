from .main import TLGeoQGISPlugin

def classFactory(iface):
    return TLGeoQGISPlugin(iface)