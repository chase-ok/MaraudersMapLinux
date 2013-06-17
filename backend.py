import requests

#login
def login(user, passwrd):
	cred = {'username': user, 'password': passwrd }
	l = requests.post("https://olinapps.herokuapp.com/api/exchangelogin", data=cred)
	user = l.json()
	sessionid = user['sessionid']
	return sessionid

#Grab session information
def start_session(sessionid):
	key = {'sessionid': sessionid}
	d =  requests.get('http://directory.olinapps.com/api/people', params=key)
	raw = d.json()
	m = requests.get('http://olinapps.com/api/me', params=key)
	profile  = m.json()
	fullname = profile['user']['id']
	fix = fullname.split('.')
	keycheck = fix[0].title() + " " + fix[1].title()	
	###Generate a dictionary linking users to their id's
	parsed = dict()
	for i in range(len(raw['people'])):
		parsed[raw['people'][i]['name']] = raw['people'][i]['id']

	return parsed[keycheck]

sessionid = login()

print start_session(sessionid)
