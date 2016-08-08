import json
import logging
import time
from pgoapi import pgoapi

with open('config.json') as file:
	config = json.load(file)
	
def accept_tos(username, password):
	api = pgoapi.PGoApi()
	api.set_position(0.0, 0.0, 0.0)
	api.login(config['auth_service'], username, password)
	time.sleep(2)
	req = api.create_request()
	req.mark_tutorial_complete(tutorials_completed = 0, send_marketing_emails = False, send_push_notifications = False)
	response = req.call()

for user in config['users']:
	accept_tos(user['username'], user['password'])
	print '{} done'.format(user['username'])