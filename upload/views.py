from django.shortcuts import render, redirect
from upload.tanf2json import tanf2json
from upload.tanfDataProcessing import processJson
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import datetime
import json
from django.apps import apps
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core import serializers
from itertools import chain
from background_task.models import Task
from background_task.models_completed import CompletedTask


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
        processJson(thefile, user)

        # redirect to status page
        return redirect('status')

    return render(request, 'upload.html')


def status(request):
    statusmap = {}
    try:
        for i in default_storage.listdir('')[1]:
            # only show files that are json and owned by the requestor
            if i.endswith('.json') and i.startswith(str(request.user)):
                # Update status if it is queued up
                taskname = 'upload.tasks.importJson'
                taskargs = {'file': i, 'user': str(request.user)}
                taskparams = json.dumps([[], taskargs])
                completedtasks = CompletedTask.objects.succeeded().filter(task_name=taskname, task_params=taskparams)
                if completedtasks.count() == 1:
                    statusmap[i] = 'Imported'
                else:
                    mytasks = Task.objects.get_task(task_name=taskname, kwargs=taskargs)
                    if mytasks.count() == 1:
                        statusmap[i] = 'Processing'
                    else:
                        # The file failed validation or is stuck.
                        # a .status file should be there to tell us whether it validated properly
                        statusfile = i + '.status'
                        try:
                            with default_storage.open(statusfile, 'r') as f:
                                status = json.load(f)
                                if len(status) == 0:
                                    statusmap[i] = 'Format Validated, Stuck'
                                else:
                                    statusmap[i] = 'Invalid Format'
                        except FileNotFoundError:
                            statusmap[i] = 'Stuck'

    except FileNotFoundError:
        print('FileNotFoundError:  hopefully this is local dev env')

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
    try:
        with default_storage.open(statusfile, 'r') as f:
            status = json.load(f)
    except FileNotFoundError:
        status = ['File processing was interrupted:  data was not imported',
                  'You will probably want to delete and re-import this file.']
    return render(request, "fileinfo.html", {'status': status})


def deletesuccessful(request):
    files = []
    for i in default_storage.listdir('')[1]:
        # only look at files that are json and owned by the requestor
        if i.endswith('.json') and i.startswith(str(request.user)):
            statusfile = i + '.status'
            try:
                with default_storage.open(statusfile, 'r') as f:
                    status = json.load(f)
                    # if there are no issues, add it to the list
                    if len(status) == 0:
                        files.append(i)
            except FileNotFoundError:
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
        with default_storage.open(statusfile, 'r') as f:
            status = json.load(f)
    except:
        # XXX probably should say something here about failing to the user
        return redirect('status')

    # Get a confirmation if we still have issues with the upload.
    # Otherwise, the import went well, so delete without prompting.
    if confirmed is None and len(status) > 0:
        return render(request, "delete.html", {'file': file, 'statusitems': len(status)})

    if default_storage.exists(file) and default_storage.exists(statusfile):
        default_storage.delete(file)
        default_storage.delete(statusfile)

    return redirect('status')


# Look at various things in the tables
def viewTables(request):
    # choose what table to view
    tablelist = []
    for model in apps.all_models['upload']:
        tablelist.append(model)
    table = request.GET.get('table')
    if table is None:
        table = tablelist[0]

    # Get the model for the selected table and get all the data from it.
    mymodel = apps.get_model('upload', table)
    alldata = mymodel.objects.all()

    # set up pagination here
    hitsperpagelist = ['All', '20', '100', '200', '500']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    page_no = request.GET.get('page')
    if hitsperpage == 'All':
        # really don't get all of them.  That could be bad.
        paginator = Paginator(alldata, 1000000)
    else:
        paginator = Paginator(alldata, int(hitsperpage))
    try:
        page = paginator.get_page(page_no)
    except PageNotAnInteger:
        page = paginator.get_page(1)
    except EmptyPage:
        page = paginator.get_page(paginator.num_pages)
    data = serializers.serialize("python", page)
    fields = []
    for field in mymodel._meta.get_fields():
        # XXX this seems messy, but the serializer doesn't emit this field
        # So we need to get rid of it to make the fields align in the table.
        if field.verbose_name != 'ID':
            fields.append(field.verbose_name)

    context = {
        'tablelist': tablelist,
        'selected_table': table,
        'data': data,
        'page': page,
        'fields': fields,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
    }
    return render(request, "viewData.html", context)


def viewquarter(request):
    # enumerate all the available calendarquarters in all tables.
    # XXX seems like it might be dangerous at scale, in case it
    # XXX requires full table scans to fulfill these queries.
    calquarters = []
    for model in apps.all_models['upload']:
        mymodel = apps.get_model('upload', model)
        calquarters = list(set().union(calquarters, mymodel.objects.values_list('calendar_quarter', flat=True)))
    calquarters.sort()
    calquarter = request.GET.get('calquarter')
    if calquarter is None:
        calquarter = calquarters[0]

    # select all data for the selected calquarter
    qslist = []
    for model in apps.all_models['upload']:
        mymodel = apps.get_model('upload', model)
        newdata = mymodel.objects.filter(calendar_quarter=calquarter).values_list()
        qslist.append(newdata)
    # XXX somehow this is not working?
    data = list(chain(*qslist))

    # set up pagination here
    hitsperpagelist = ['All', '20', '100', '200', '500']
    hitsperpage = request.GET.get('hitsperpage')
    if hitsperpage is None:
        hitsperpage = hitsperpagelist[1]
    page_no = request.GET.get('page')
    if hitsperpage == 'All':
        # really don't get all of them.  That could be bad.
        paginator = Paginator(data, 1000000)
    else:
        paginator = Paginator(data, int(hitsperpage))
    try:
        page = paginator.get_page(page_no)
    except PageNotAnInteger:
        page = paginator.get_page(1)
    except EmptyPage:
        page = paginator.get_page(paginator.num_pages)

    context = {
        'calquarters': calquarters,
        'selected_calqarter': calquarter,
        'page': page,
        'hitsperpagelist': hitsperpagelist,
        'selected_hitsperpage': hitsperpage,
    }
    return render(request, "viewcalquarter.html", context)
