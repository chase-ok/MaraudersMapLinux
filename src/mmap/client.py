
import requests

class ClientError(Exception): pass

def _wrap_requests_error(error_cls):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                raise error_cls(e)
            except KeyError as e:
                raise error_cls(e)
        return wrapper
    return decorator

def make_connection(user, password):
    session_id = _start_session(user, password)
    return Connection(session_id)

class UnableToStartSession(ClientError): pass
LOGIN_URL = "https://olinapps.herokuapp.com/api/exchangelogin"
@_wrap_requests_error(UnableToStartSession)
def _start_session(user, password):
    credentials = {'username':user, 'password':password}
    request = requests.post(LOGIN_URL, data=credentials)
    request.raise_for_status()
    return request.json()['sessionid']


BINDS_URL = "http://map.olinapps.com/api/binds"
class UnableToGetNearestBinds(ClientError): pass

POSITIONS_URL = "http://map.olinapps.com/api/positions"
class UnableToPostPosition(ClientError): pass

USER_URL = "http://directory.olinapps.com/api/me"
class UnableToGetUserId(ClientError): pass


class Connection(object):

    def __init__(self, session_id):
        self.session_id = session_id

    def _with_session(self, **params):
        params['sessionid'] = self.session_id
        return params
    
    @_wrap_requests_error(UnableToGetUserId)
    def get_user_id(self):
        request = requests.get(USER_URL, params=self._with_session())
        request.raise_for_status()
        return request.json()['id']

    @_wrap_requests_error(UnableToGetNearestBinds)
    def get_nearest_binds(self, cells):
        params = dict(cell.binding_pair for cell in cells)
        request = requests.get(BINDS_URL, params=self._with_session(**params))
        request.raise_for_status()
        return map(Bind.from_json, request.json()['binds'])

    @_wrap_requests_error(UnableToPostPosition)
    def post_position(self, bind_id):
        request = requests.post(POSITIONS_URL, 
                                params=self._with_session(bind=bind_id))
        request.raise_for_status()

class Place(object):

    @staticmethod
    def from_json(json):
        return Place(**json)

    def __init__(self, id=None, name=None, floor=None, alias=None):
        self.id = id
        self.name = name
        self.floor = floor 
        self.alias = alias

    def __repr__(self):
        return "Place(id='{0}', name='{1}', floor='{2}', alias='{3}')"\
               .format(self.id, self.name, self.floor, self.alias)

class Bind(object):

    @staticmethod
    def from_json(json):
        json = json.copy()
        json['place'] = Place.from_json(json['place'])
        return Bind(**json)

    def __init__(self, id=None, place=None, signals=None, username=None, 
                 x=None, y=None):
        self.id = id
        self.place = place
        self.signals = signals
        self.username = username
        self.x = x
        self.y = y

    def __repr__(self):
        return "Bind(id='{0}', place={1}, signals={2}, username='{3}', x={4}, y={5})"\
               .format(self.id, self.place, self.signals, self.username, 
                       self.x, self.y)

