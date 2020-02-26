# Standard library imports
import datetime

# Third party imports
import dateutil.parser

# Local application imports
# local imports
# vendored dependencies

def get_next_delivery(date, deliveries, username):
    deliveries = get_next_deliveries(date, deliveries, username)
    sorted_deliveries = sorted(deliveries, key=lambda d: dateutil.parser.isoparse(d['date']))
    if len(sorted_deliveries) > 0:
        return sorted_deliveries[0]
    return None

def get_next_deliveries(date, deliveries, username):
    deliveries = get_deliveries_for_username(deliveries, username)
    return [d for d in deliveries if dateutil.parser.isoparse(d['date']) > date]

def get_deliveries_for_username(deliveries, username):
    retList = []
    for delivery in deliveries:
        if delivery['status'] == 'ready':
            for user in delivery['users']:
                if user['uid'] == username:
                    retVal = {}
                    retVal['name'] = delivery['name']
                    retVal['date'] = delivery['date']
                    retVal['delivery'] = user['delivery']
                    retList.append(retVal)
    return retList


def get_recent_deliveries(date, deliveries, username):
    deliveries = get_deliveries_for_username(deliveries, username)
    return [d for d in deliveries if dateutil.parser.isoparse(d['date']) < date]
