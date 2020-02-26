# Standard library imports
import unittest
from functools import reduce
import json
from datetime import datetime

# Third party imports
import pytz

# Local application imports
import delivery_tools
# local imports

# vendored dependencies
# none


class import_data(object):
    def __init__(self, filename):
        self.filename = filename

    def __call__(self, func):
        def func_wrapper(*args):
            with open(self.filename, 'r') as json_file:
                parsed_json = json.loads(json_file.read())
                func(*args, parsed_json=parsed_json)
        return func_wrapper


class DeliveryTests(unittest.TestCase):
    @import_data('test/test_deliveries.json')
    def test_recent_deliveries(self, parsed_json):
        naive_current_date = datetime(2020, 1, 28)
        current_date = pytz.utc.localize(naive_current_date)
        deliveries = delivery_tools.get_recent_deliveries(current_date, parsed_json, "user0002")
        self.assertEqual(len(deliveries), 2)


    @import_data('test/test_deliveries.json')
    def test_next_deliveries(self, parsed_json):
        naive_current_date = datetime(2020, 1, 28)
        current_date = pytz.utc.localize(naive_current_date)
        deliveries = delivery_tools.get_next_deliveries(current_date, parsed_json, "user0002")
        self.assertEqual(len(deliveries), 2)

    @import_data('test/test_deliveries.json')
    def test_next_delivery(self, parsed_json):
        naive_current_date = datetime(2020, 1, 28)
        current_date = pytz.utc.localize(naive_current_date)
        deliveries = delivery_tools.get_next_delivery(current_date, parsed_json, "user0002")
        self.assertEqual('2020-02-04T11:38:59.612Z', deliveries['date'])

    @import_data('test/test_deliveries.json')
    def test_get_deliveries_for_username(self, parsed_json):
        deliveries = delivery_tools.get_deliveries_for_username(parsed_json, "user0002")
        self.assertEqual(len(deliveries), 4)

        deliveries = delivery_tools.get_deliveries_for_username(parsed_json, "user0001")
        self.assertEqual(len(deliveries), 4)


if __name__ == '__main__':
    unittest.main()
