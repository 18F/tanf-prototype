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
* Set up the database:  `NOLOGINGOV=TRUE DEBUG=true ./manage.py migrate`
* Create a superuser: `NOLOGINGOV=TRUE DEBUG=true ./manage.py createsuperuser`  Add your
  email address.
* Run the app!  `NOLOGINGOV=TRUE DEBUG=true ./manage.py runserver`
* You should be able to access the app on http://localhost:8000/

### Testing
All good applications should be tested.  Here's how you can execute the tests after your
environment is set up:

`./test.sh`

The python test suites should run and exit cleanly.

## Run this on cloud.gov

You can also deploy this application on [cloud.gov](https://cloud.gov/).
* You will need to get [credentials for cloud.gov](https://cloud.gov/signup/), as
  well as [set up the command line cf utility](https://cloud.gov/docs/getting-started/setup/#set-up-the-command-line).
* Once you have your credentials and are logged in, `./deploy-cloudgov.sh setup`
  sets up all the services required and sets up the database.
* If you want to deploy this with login.gov authentication, you will need to
  [register with login.gov as a developer](https://developers.login.gov).
  You will also need to create a new test app in the integration dashboard for
  the prototype app.  Eventually when you go to production, you will need to
  work with the login.gov staff to get your app enabled for their production IDP.
  You will need to:
	* Paste in the contents of the `cert.pem` file that was created during the setup
  	  above as the public certificate.
  	* Create an Issuer ID for your app.
  	* Add URLs for "Return to app URL" and "Redirect URIs".  The former should be
  	  something like https://tanf-fantastic-waterbuck.app.cloud.gov/about/, and the
  	  latter should have something like https://tanf-fantastic-waterbuck.app.cloud.gov/openid/callback/login/
  	  and https://tanf-fantastic-waterbuck.app.cloud.gov/openid/callback/logout/.
  You will also need to set some environment variables:
  	* `cf set-env tanf OIDC_RP_CLIENT_ID <Issuer ID>`
  	* `cf set-env tanf JWT_KEY "$(cat key.pem)"`
* Create a superuser for you to log in with:  `./deploy-cloudgov.sh createsuperuser your@email.gov`
* If you want to deploy without login.gov integration:  `cf set-env tanf NOLOGINGOV True`
  Note:  this will make it so that anybody can supply an email address and password and
  get in.  It basically disables authentication.

### Updating the App in cloud.gov by hand

If you want to update the app, run `./deploy-cloudgov.sh` to push the changes
up that are in your current directory.  Database migrations will automatically be
run after each deploy.  This will cause a minute or two of downtime.

### Set up CI/CD

First, make sure that you have already run all the setup to get the app going in
cloud.gov.

This is set up to run in [CircleCI](https://circleci.com/).  There is a
`.circleci/config.yml` file which drives this.  If you need to use another CI/CD system,
feel free to look at this file.  It should be fairly simple to translate this to whatever
system you need to do this with.

To enable this, go to [CircleCI](https://circleci.com/), log in, and click on "Add Projects".
Find this github repo and enable builds on it.  Then, add the following environment variables
to the build settings:
* `CF_ORG`:  This is your cloud.gov org that you are deploying this to.
* `CF_SPACE`:  This is the space in cloud.gov that you wish to deploy this to.
* `CF_USERNAME`:  This is the username that you can get with the `cf service-key tanf deployer` command
* `CF_PASSWORD`:  This is the password that you can get with the `cf service-key tanf deployer` command

Once all this is set up, you can create branches and commit code to them,
and it will run the tests for you  You can see the results in github, and you can click through to
see what went wrong if there is a problem.

Once your code is complete and passes tests, you can create a Pull Request (often called a PR)
to ask that your code be merged into master.  Once that Pull Request has been approved
and merged in, circleci will do a full build/test/deploy to the cloud.gov account that you
set up.

## Connect to the database in cloud.gov

First, you will need to install the [cf connect-to-service plugin](https://github.com/18F/cf-service-connect).

After this is installed, you can get into the database in cloud.gov by doing
`cf connect-to-service tanf tanf-db`.
This will give you a postgres psql prompt, and you can do whatever queries you want.
The `upload_*` tables are what contain all the data.

If you would like to connect a GUI client to the database, then you can run
`cf connect-to-service --no-client tanf tanf-db`, and it will supply you with the host/port,
username/password, and database name for you to configure your client to use. 

Note:
the credentials will only work and the database will only be accessible while
you have your authenticated `connect-to-service` session going.
