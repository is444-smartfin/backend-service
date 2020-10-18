import unittest
import json

from digibank import app

class ApiTest(unittest.TestCase):
    # setUp has to be capitalised this way, see https://docs.python.org/3/library/unittest.html
    def setUp(self):
        self.app = app.test_client()

    def test_square(self):
        # Input
        payload = json.dumps({
            "input": 5
        })

        # What to test
        response = self.app.post('/square', headers={"Content-Type": "application/json"}, data=payload)

        # Assert
        self.assertEqual(int, type(response.json))
        self.assertEqual(25, response.json)
        self.assertEqual(200, response.status_code)

    def tearDown(self):
        pass