import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json_logic


# This is where we process the json file
def processJson(file):
	if validateJson(file):
		importJson(file)

def validateJson(file):
	statusfile = file + '.status'
	issues = []
	try:
		with default_storage.open(file,'r') as f:
			data = json.load(f)

			# XXX first test rule
			if data['header']['calendarquarter'].startswith('1972'):
				issues.append('calendarquarter is too early: ' + data['header']['calendarquarter'])

			# XXX fill out more rules here.  Probably with a rules file and json_logic?
	except:
		issues = ['ERROR:  could not open file!']

	default_storage.save(statusfile, ContentFile(json.dumps(issues)))

	return len(issues) == 0

def importJson(file):
	# XXX need to actually import the data into the db
	print('importing json')
	return
