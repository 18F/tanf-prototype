from django.shortcuts import render, redirect
from django.http import HttpResponse
from upload.tanf2json import tanf2json
from upload.tanfDataProcessing import processJson
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import datetime

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
		filename = user + datestr + '.json'
		queuedfile = default_storage.save(filename, ContentFile(tanfdata))

		# process file
		processJson(queuedfile)

		# redirect to status page
		return redirect('status')

	return render(request, 'upload.html')

def status(request):
	files = default_storage.listdir('')[1]
	files.sort
	context = {
		'queuedfiles': files
	}
	return render(request, "status.html", context)
