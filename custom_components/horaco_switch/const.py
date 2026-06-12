"""Constants for the HORACO Managed Switch integration."""

DOMAIN = "horaco_switch"

DEFAULT_PORT = 80
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_SCAN_INTERVAL = 30  # seconds

CONF_SCAN_INTERVAL = "scan_interval"

# CGI endpoints — same as byte4geek/switch-dashboard
CGI_LOGIN     = "/login.cgi"
CGI_INFO      = "/info.cgi"
CGI_PORT_STATS = "/port.cgi?page=stats"
CGI_PORT_CFG  = "/port.cgi"
CGI_REBOOT    = "/reboot.cgi"

# Port status values
PORT_STATUS_UP       = "up"
PORT_STATUS_DOWN     = "down"
PORT_STATUS_DISABLED = "disable"
