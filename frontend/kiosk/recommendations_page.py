from kiosk.catalog_page import build_catalog
from core.constants import Routes
def build(page): return build_catalog(page, Routes.RECOMMENDATIONS, "Recommended For You", "Personalized when you scan your library QR; otherwise based on available catalog titles.", "personalized")
