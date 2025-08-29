DOMAIN = "vitesy_shelfy"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# OAuth2 client values (based on app traffic)
CLIENT_ID = "79r5m89hpavjbas5eadaif9tf"
REDIRECT_URI = "hub.vitesy.com:/oauth2redirect"
SCOPE = "openid email profile aws.cognito.signin.user.admin API/*:*"

# API base URLs
AUTH_BASE_URL = "https://auth.vitesy.com"
API_BASE_URL = "https://v1.api.vitesyhub.com"

# Endpoints
LOGIN_URL = f"{AUTH_BASE_URL}/login"
TOKEN_URL = f"{AUTH_BASE_URL}/oauth2/token"
ME_URL = f"{API_BASE_URL}/users/me"
DEVICES_URL = f"{API_BASE_URL}/devices"
MEASUREMENTS_URL = f"{API_BASE_URL}/measurements"
MAINTENANCE_URL_TEMPLATE = f"{API_BASE_URL}/devices/{{device_id}}/maintenance"

# Other
DEFAULT_SCAN_INTERVAL = 300  # seconds
OAUTH_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}
