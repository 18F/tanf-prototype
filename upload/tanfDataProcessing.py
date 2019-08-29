import json
from django.core.files.storage import default_storage


# This is where we process the json file
def processJson(file):
	if validateJson(file):
		importJson(file)

def validateJson(file):
	# XXX
	print('validating json')
	return True

def importJson(file):
	# XXX
	print('importing json')
	pass
