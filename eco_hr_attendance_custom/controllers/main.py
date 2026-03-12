import requests
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAttendanceAccurateController(http.Controller):

    def _get_real_city_name(self, lat, lon):
        _logger.info("DEBUG: Calling Nominatim API for Lat: %s, Lon: %s", lat, lon)
        try:
            # Added a more unique User-Agent to avoid being blocked by Nominatim
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
            headers = {'User-Agent': 'OdooAttendanceDebug_EcoTech'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                _logger.info("DEBUG: Nominatim Full Response: %s", data)
                address = data.get('address', {})
                city = address.get('city') or address.get('town') or address.get('suburb') or address.get('state') or _(
                    'Unknown')
                _logger.info("DEBUG: Extracted City: %s", city)
                return city
            else:
                _logger.error("DEBUG: API Error Status Code: %s", response.status_code)
        except Exception as e:
            _logger.error("DEBUG: Geocoding Exception: %s", str(e))
        return _('Unknown Location')

    def _prepare_geo_data(self, mode, lat, lon):
        _logger.info("DEBUG: Preparing Geo Data. Mode: %s, Lat: %s, Lon: %s", mode, lat, lon)

        if not lat or not lon or lat in (False, 'false', None):
            _logger.warning("DEBUG: Coordinates missing or invalid.")
            raise UserError(_("High Precision GPS is required. Please allow location access."))

        real_city = self._get_real_city_name(lat, lon)

        return {
            'city': real_city,
            'country_name': _('Egypt'),
            'latitude': float(lat),
            'longitude': float(lon),
            'ip_address': request.httprequest.remote_addr,
            'browser': request.httprequest.user_agent.browser,
            'mode': mode,
        }

