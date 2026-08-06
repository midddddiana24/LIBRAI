from kiosk.catalog_page import build_catalog
from core.constants import Routes
def build(page): return build_catalog(page, Routes.NEW_BOOKS, "New Arrivals", "Recently added titles in the library collection.", "new")
