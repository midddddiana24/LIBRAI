"""
LIBRAI - Application-wide constants.

Centralizes route names, session timeouts, and other fixed values so
they are never hardcoded/duplicated across pages and components.
"""

# ----------------------------------------------------------------------
# Route names (used by core/routes.py and page navigation calls)
# ----------------------------------------------------------------------
class Routes:
    HOME = "/"
    SEARCH = "/search"
    BOOK_DETAILS = "/book"  # append /{book_id}

    BORROW_SCAN_USER = "/borrow/scan-user"
    BORROW_USER_VERIFIED = "/borrow/user-verified"
    BORROW_SCAN_BOOK = "/borrow/scan-book"
    BORROW_CONFIRM = "/borrow/confirm"
    BORROW_SUCCESS = "/borrow/success"

    RETURN_SCAN_BOOK = "/return/scan-book"
    RETURN_CONFIRM = "/return/confirm"
    RETURN_SUCCESS = "/return/success"

    AI_ASSISTANT = "/ai"
    RECOMMENDATIONS = "/recommendations"
    POPULAR_BOOKS = "/popular"
    NEW_BOOKS = "/new-books"
    ACCOUNT = "/account"
    RESERVATIONS = "/reservations"

    ADMIN_LOGIN = "/admin/login"
    ADMIN_DASHBOARD = "/admin/dashboard"
    ADMIN_BOOKS = "/admin/books"
    ADMIN_USERS = "/admin/users"
    ADMIN_BORROWINGS = "/admin/borrowings"
    ADMIN_RETURNS = "/admin/returns"
    ADMIN_RESERVATIONS = "/admin/reservations"
    ADMIN_REPORTS = "/admin/reports"
    ADMIN_AUDIT_LOGS = "/admin/audit-logs"
    ADMIN_SETTINGS = "/admin/settings"


# ----------------------------------------------------------------------
# Kiosk session behavior
# ----------------------------------------------------------------------
class Session:
    # Seconds of inactivity before the kiosk auto-resets to Home and
    # clears any authenticated user / AI conversation / scan state.
    INACTIVITY_TIMEOUT_SECONDS = 90
    # Seconds to show a "Still there?" warning before forcing a reset.
    WARNING_BEFORE_RESET_SECONDS = 15


# ----------------------------------------------------------------------
# QR scan states (shared across borrow/return scan components)
# ----------------------------------------------------------------------
class QRScanState:
    WAITING = "waiting"
    DETECTING = "detecting"
    DETECTED = "detected"
    INVALID = "invalid"
    USER_INACTIVE = "user_inactive"
    CONNECTION_ERROR = "connection_error"


# ----------------------------------------------------------------------
# Generic async/request states used by every service-backed view
# ----------------------------------------------------------------------
class RequestState:
    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    VALIDATION_ERROR = "validation_error"
    AUTH_ERROR = "auth_error"
    PERMISSION_ERROR = "permission_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    EMPTY = "empty"


# ----------------------------------------------------------------------
# Speech / voice search states
# ----------------------------------------------------------------------
class SpeechState:
    READY = "ready"
    LISTENING = "listening"
    PROCESSING = "processing"
    COMPLETE = "complete"
    PERMISSION_DENIED = "permission_denied"
    UNAVAILABLE = "unavailable"


APP_NAME = "LIBRAI"
APP_TAGLINE = "AI-Powered Library Kiosk"
