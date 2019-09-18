import json
from django.core.files.storage import default_storage
from upload.models import Family, Adult, Child, ClosedPerson, AggregatedData, FamiliesByStratumData
from django.db import transaction
from background_task import background
from upload.tanfDataProcessing import tanf2db
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder


# This is for tasks that need to be run in the background.
class TANFDataImport(Exception):
    pass


@background
def importRecords(file=None, user=None):
    print('starting to process', file)
    statusfile = file + '.status'
    status = {'status': 'Importing'}
    default_storage.save(statusfile, ContentFile(json.dumps(status).encode()))
    invalidcount = 0

    # wrap this whole thing in a transaction.  If we encounter problems
    # importing data, or we have invalid records, store the invalid records
    # and then rollback.
    try:
        with transaction.atomic():
            try:
                with default_storage.open(file, 'r') as f:
                    tanf2db(f, user)
            except FileNotFoundError:
                print('missing file, assuming job was deleted before we could process it:', file)
                return
            except:
                status = {'status': 'Error While Importing'}
                default_storage.delete(statusfile)
                default_storage.save(statusfile, ContentFile(json.dumps(status).encode()))
                raise TANFDataImport('Error While Importing')

            print('finished importing', file)

            # check if we had any invalid things
            invalidcount = Family.objects.filter(valid=False).count()
            invalidcount += Adult.objects.filter(valid=False).count()
            invalidcount += Child.objects.filter(valid=False).count()
            invalidcount += ClosedPerson.objects.filter(valid=False).count()
            invalidcount += AggregatedData.objects.filter(valid=False).count()
            invalidcount += FamiliesByStratumData.objects.filter(valid=False).count()
            if invalidcount > 0:
                status = {'status': 'Failed Validation'}
                default_storage.delete(statusfile)
                default_storage.save(statusfile, ContentFile(json.dumps(status).encode()))

                # Write out an invalid file with all the invalid stuff.
                invalidfile = file + '.invalid'
                with default_storage.open(invalidfile, 'w') as f:
                    f.write('[')
                    for i in Family.objects.filter(valid=False).values():
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    for i in Adult.objects.filter(valid=False):
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    for i in Child.objects.filter(valid=False):
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    for i in ClosedPerson.objects.filter(valid=False):
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    for i in AggregatedData.objects.filter(valid=False):
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    for i in FamiliesByStratumData.objects.filter(valid=False):
                        f.write(json.dumps(list(i), cls=DjangoJSONEncoder))
                    f.write(']')
                raise TANFDataImport('invalid records: rolling back')
            else:
                status = {'status': 'Imported'}
                default_storage.delete(statusfile)
                default_storage.save(statusfile, ContentFile(json.dumps(status).encode()))
    except TANFDataImport as e:
        # if we have a data import/validation problem, it should be rolled
        # back and then we should exit the job cleanly so that we don't
        # reschedule the job and run it again.
        print('Data import/validation did not succeed:', e)
        pass
    return
