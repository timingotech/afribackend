from django.test import override_settings
from rest_framework.test import APITestCase
from unittest.mock import patch, Mock


@override_settings(TRIP_BASE_FARE=2000.0, TRIP_PER_KM=500.0, TRIP_PER_MIN=50.0, TRIP_MIN_FARE=4000.0)
class EstimateFareTests(APITestCase):
    def test_estimate_direct(self):
        """When distance and duration supplied, estimate should return computed fare (respect minimum)."""
        resp = self.client.post('/api/trips/estimate/', {'distance_km': 1.0, 'duration_min': 10}, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('estimated_fare', data)
        # base(2000) + per_km(500*1) + per_min(50*10) = 3000 -> min fare 4000 enforced
        self.assertEqual(float(data['estimated_fare']), 4000.0)

    @patch('apps.trips.views.requests.get')
    def test_estimate_route_osrm(self, mock_get):
        """When origin/dest supplied, view should call OSRM and compute estimate from returned distance/duration."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        # distance in meters, duration in seconds
        mock_resp.json.return_value = {'routes': [{'distance': 2000, 'duration': 600}]}
        mock_get.return_value = mock_resp

        payload = {'origin_lat': 6.5244, 'origin_lng': 3.3792, 'dest_lat': 6.4275, 'dest_lng': 3.4721}
        resp = self.client.post('/api/trips/estimate/route/', payload, format='json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('estimated_fare', data)
        # distance 2km, duration 10min -> calculated 3500 -> min enforced 4000
        self.assertEqual(float(data['estimated_fare']), 4000.0)
