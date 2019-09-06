import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from upload.models import Family, Adult, Child
from datetime import datetime


# This is where we process the json file
def processJson(file, user):
    if validateJson(file):
        importJson(file, user)


def validateJson(file):
    statusfile = file + '.status'
    issues = []
    try:
        with default_storage.open(file, 'r') as f:
            data = json.load(f)

            # XXX first test rule
            if data['header']['calendarquarter'].startswith('1972'):
                issues.append('calendarquarter is too early: ' + data['header']['calendarquarter'])

            # XXX fill out more rules here.  Probably with a rules file and json_logic?
    except:
        issues = ['ERROR:  could not open file!']

    default_storage.save(statusfile, ContentFile(json.dumps(issues).encode()))

    return len(issues) == 0


def importJson(file, user):
    data = {}
    with default_storage.open(file, 'r') as f:
        data = json.load(f)

    now = datetime.now()

    # import families
    for i in data['section1_familydata']:
        # first fix up stuff that doesn't fit or requires parsing.
        del i['blank']
        i['countyfipscode'] = int(i['countyfipscode'])

        # import the family into the db
        family = Family.objects.create(
            imported_at=now,
            imported_by=user,
            calendar_quarter=data['header']['calendarquarter'],
            state_code=data['header']['statefipscode'],
            tribe_code=data['header']['tribecode'],
            # This is where all the json data gets added in
            **i
            )
        family.save()

    # import adults
    for i in data['section1_adultdata']:
        # first fix up stuff that doesn't fit or requires parsing.
        # del i['blank']
        i['dateofbirth'] = datetime.strptime(i['dateofbirth'], '%Y%m%d').strftime('%Y-%m-%d')

        # import the adult into the db
        adult = Adult.objects.create(
            imported_at=now,
            imported_by=user,
            calendar_quarter=data['header']['calendarquarter'],
            state_code=data['header']['statefipscode'],
            tribe_code=data['header']['tribecode'],
            # This is where all the json data gets added in
            **i
            )
        adult.save()

    # import children
    for i in data['section1_childdata']:
        # first fix up stuff that doesn't fit or requires parsing.
        # del i['blank']
        i['dateofbirth'] = datetime.strptime(i['dateofbirth'], '%Y%m%d').strftime('%Y-%m-%d')

        # import the child into the db
        child = Child.objects.create(
            imported_at=now,
            imported_by=user,
            calendar_quarter=data['header']['calendarquarter'],
            state_code=data['header']['statefipscode'],
            tribe_code=data['header']['tribecode'],
            # This is where all the json data gets added in
            **i
            )
        child.save()

    return
