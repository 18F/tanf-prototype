import json
from django.core.files.storage import default_storage
from upload.models import Family, Adult, Child
from datetime import datetime
from django.db import transaction
from background_task import background


# This is for tasks that need to be run in the background.

@background
@transaction.atomic
def importJson(file=None, user=None):
    data = {}
    with default_storage.open(file, 'r') as f:
        data = json.load(f)

    now = datetime.now()

    # import families
    for i in data['section1_familydata']:
        # first fix up stuff that doesn't fit or requires parsing.
        try:
            del i['blank']
        except KeyError:
            pass
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

    # XXX add more record types below here
    return
