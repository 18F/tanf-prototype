# TANF Data Reporting Prototype

This repo has a prototype for a TANF Data Reporting system, where States,
Territories, and Tribes can upload TANF data and get it validated and stored
in a database.

## Run this locally

To do local development, you can run this application on your local system.  Here is how
to get this going:
* Make sure that python3 is running on your system.  You can consult one of the
  many guides on the Internet on how to do this, but here's one that has some good
  links:  [Properly Installing Python](https://docs.python-guide.org/starting/installation/)
* Install all the python requirements in a venv: 
  `python3 -m venv venv ; . venv/bin/activate ; pip install -r requirements.txt`
* Run the app!  `DEBUG=True ./manage.py runserver`

### Testing
All good applications should be tested.  Here's how you can execute the tests after your
environment is set up:

`./manage.py test`

## Run this on cloud.gov

You can also deploy this application on [cloud.gov](https://cloud.gov/).
* You will need to get [credentials for cloud.gov](https://cloud.gov/signup/).
* Once you have your credentials and are logged in, `./deploy-cloudgov.sh setup`
  sets up all the services required.
* The first time you start this system up, you will need to set up the database
  with `cf run-task tanf "python manage.py migrate"`.

If you want to update the app, or integrate with CI/CD to automatically push code:
* Run `./deploy-cloudgov.sh` to push the changes up.
* If you also have database schema changes (new columns or changes to existing ones),
  you will need to re-run `cf run-task tanf "python manage.py migrate"`.

You can get into the database by doing `cf connect-to-service tanf tanf-db`.
This will give you a postgres psql prompt, and you can do whatever queries you want.
The `upload_*` tables are what contain all the data.
