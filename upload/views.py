from django.shortcuts import render, redirect
from django.http import HttpResponse
from upload.tanf2json import tanf2json
from upload.tanfDataProcessing import processJson
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import datetime
import json

# Create your views here.

def about(request):
	return render(request, "about.html")


def upload(request):
	if request.method == 'POST' and request.FILES['myfile']:
		myfile = request.FILES['myfile']
		tanfdata = tanf2json(myfile)

		# store tanfdata for processing
		user = str(request.user)
		datestr = datetime.datetime.now().strftime('%Y%m%d%H%M%SZ')
		originalname = myfile.name
		filename = '_'.join([user, datestr, originalname, '.json'])
		thefile = default_storage.save(filename, ContentFile(tanfdata.encode()))

		# process file (validate and store if validation is successful)
		# XXX If this takes too long to process inline, we will have
		# XXX to change the code to just store the file and to kick off
		# XXX a job to process the data.  Other pages will need some
		# XXX extra code to handle unprocessed jobs too.
		processJson(thefile, user)

		# redirect to status page
		return redirect('status')

	return render(request, 'upload.html')


def status(request):
	statusmap = {}
	for i in default_storage.listdir('')[1]:
		# only show files that are json and owned by the requestor
		if i.endswith('.json') and i.startswith(str(request.user)):
			statusfile = i + '.status'
			try:
				with default_storage.open(statusfile,'r') as f:
					status = json.load(f)
					if len(status) == 0:
						statusmap[i] = 'Pass'
					else:
						statusmap[i] = 'Fail'
			except:
					statusmap[i] = 'Stuck'

	files = sorted(statusmap.items())

	context = {
		'filelist': files,
	}
	return render(request, "status.html", context)


# This is where we should be able to delve in and edit data that needs fixing.
# For now, we will just show the issues, so they can reupload.  Maybe this is
# better, because this will enforce good data hygiene on the STT end?
def fileinfo(request, file=None):
	status = []
	statusfile = file + '.status'
	with default_storage.open(statusfile,'r') as f:
		status = json.load(f)
	return render(request, "fileinfo.html", {'status': status})


def deletesuccessful(request):
	files = []
	for i in default_storage.listdir('')[1]:
		# only look at files that are json and owned by the requestor
		if i.endswith('.json') and i.startswith(str(request.user)):
			statusfile = i + '.status'
			try:
				with default_storage.open(statusfile,'r') as f:
					status = json.load(f)
					# if there are no issues, add it to the list
					if len(status) == 0:
						files.append(i)
			except:
				pass
	for file in files:
		statusfile = file + '.status'
		if default_storage.exists(file) and default_storage.exists(statusfile):
			default_storage.delete(file)
			default_storage.delete(statusfile)
	return redirect('status')


def delete(request, file=None):
	confirmed = request.GET.get('confirmed')
	statusfile = file + '.status'

	try:
		with default_storage.open(statusfile,'r') as f:
			status = json.load(f)
	except:
		# XXX probably should say something here about failing to the user
		return redirect('status')

	# Get a confirmation if we still have issues with the upload.
	# Otherwise, the import went well, so delete without prompting.
	if confirmed == None and len(status) > 0:
		return render(request, "delete.html", {'file': file, 'statusitems': len(status)})

	if default_storage.exists(file) and default_storage.exists(statusfile):
		default_storage.delete(file)
		default_storage.delete(statusfile)

	return redirect('status')
