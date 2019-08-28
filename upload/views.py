from django.shortcuts import render
from django.http import HttpResponse
from upload.tanf2json import tanf2json


# Create your views here.

def about(request):
	context = {
	}
	return render(request, "about.html", context=context)

def upload(request):
	context = {
		'tanfdata': '',
	}
	if request.method == 'POST' and request.FILES['myfile']:
		myfile = request.FILES['myfile']
		# XXX should actually store this in a durable location first, then go select it for processing.
		tanfdata = tanf2json(myfile)
		context['tanfdata'] = str(tanfdata)

	return render(request, 'upload.html', context)
