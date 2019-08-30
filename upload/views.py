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
	queuedfile = ''
	if request.method == 'POST' and request.FILES['myfile']:
		myfile = request.FILES['myfile']
		tanfdata = tanf2json(myfile)

		# store tanfdata in queue for processing
		user = str(request.user)
		datestr = datetime.datetime.now().strftime('%Y%m%d%H%M%SZ')
		originalname = myfile.name
		filename = '_'.join([user, datestr, originalname, '.json'])
		queuedfile = default_storage.save(filename, ContentFile(tanfdata))

		# process file
		processJson(queuedfile)

		# redirect to status page
		return redirect('status')

	return render(request, 'upload.html')


def status(request):
	files = []
	for i in default_storage.listdir('')[1]:
		# only show files that are json and owned by the requestor
		if i.endswith('.json') and i.startswith(str(request.user)):
			files.append(i)
	files.sort
	context = {
		'queuedfiles': files
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


def delete(request, file=None):
	confirmed = request.GET.get('confirmed')
	statusfile = file + '.status'

	with default_storage.open(statusfile,'r') as f:
		status = json.load(f)

	# Get a confirmation if we still have issues with the upload.
	# Otherwise, the import went well, so delete without prompting.
	if confirmed == None and len(status) > 0:
		return render(request, "delete.html", {'file': file, 'statusitems': len(status)})

	if default_storage.exists(file) and default_storage.exists(statusfile):
		default_storage.delete(file)
		default_storage.delete(statusfile)

	return redirect('status')
