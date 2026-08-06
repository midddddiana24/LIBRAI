from kiosk.catalog_page import build_catalog
from core.constants import Routes
def build(page): return build_catalog(page, Routes.POPULAR_BOOKS, "Popular Books", "Books readers are borrowing most often.", "popular")
