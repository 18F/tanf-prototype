#!/bin/sh
#
# This script will deploy the app to cloud.gov.  There are a few different
# ways to execute this script:
# 
# './deploy-cloudgov.sh':  This will just do a default deploy of the app.
#
# './deploy-cloudgov.sh resetkeys':  This will reset the keys used for UAA
# authentication.
# 
# './deploy-cloudgov.sh setup': this will set up all the services required
# to get it going first.
#
# `./deploy-cloudgov.sh zdt':  This will do a zero-downtime deploy of the
# service.  It is meant to be used by a CI/CD deploy system.
# 
# `./deploy-cloudgov.sh dbsetup':  This will kick off a job that will do a
# django db migration.  This can be done by hand, or with CI/CD.
#

# function to check if a service exists
service_exists()
{
  cf service "$1" >/dev/null 2>&1
}

if [ "$1" = "setup" ] ; then  echo
	# create services (if needed)
	if service_exists "tanf-storage" ; then
	  echo tanf-storage already created
	else
	  if [ "$2" = "prod" ] ; then
	    cf create-service s3 basic tanf-storage
	  else
	    cf create-service s3 basic-sandbox tanf-storage
	  fi
	fi

	if service_exists "tanf-uaa-client" ; then
		echo tanf-uaa-client alredy created
	else
		cf create-service cloud-gov-identity-provider oauth-client tanf-uaa-client
	fi

	if service_exists "tanf-deployer" ; then
	  echo tanf-deployer already created
	else
	  cf create-service cloud-gov-service-account space-deployer tanf
	  cf create-service-key tanf deployer
	  echo "to get the CF_USERNAME and CF_PASSWORD, execute 'cf service-key tanf deployer'"
	fi

	if service_exists "tanf-db" ; then
	  echo tanf-db already created
	else
	  if [ "$2" = "prod" ] ; then
	    cf create-service aws-rds medium-psql-redundant tanf-db
	  else
	    cf create-service aws-rds shared-psql tanf-db
	  fi
	  echo sleeping until db is awake
	  for i in 1 2 3 ; do
	  	sleep 60
	  	echo $i minutes...
	  done
	fi
fi

# launch the app
if [ "$1" = "zdt" ] ; then
	# Do a zero downtime deploy.  This requires enough memory for
	# two tanf apps to exist in the org/space at one time.
	if cf plugins | grep blue-green-deploy >/dev/null ; then
		echo blue-green-deploy plugin already installed
	else
		echo "installing blue-green-deploy plugin"
		cf add-plugin-repo CF-Community https://plugins.cloudfoundry.org
		cf install-plugin blue-green-deploy -r CF-Community -f
	fi
	cf blue-green-deploy tanf -f manifest.yml --delete-old-apps || exit 1
else
	cf push || exit 1
fi

# do db migrations if requested
if [ "$1" = "dbsetup" ] ; then
	cf run-task tanf "python manage.py migrate" --name dbsetup
fi

# set up OIDC stuff
ROUTE="$(cf apps | grep tanf | awk '{print $6}')"
if cf e tanf | grep -q UAA_CLIENT_SECRET && [ "$1" = "resetkeys" ] ; then
	echo 'UAA already set up'
else
	if [ -z "$ROUTE" ] ; then
		echo "cannot create OIDC service key until the app has been created."
		echo "Get the app running and then re-run the setup"
	else
		echo "resetting UAA variables"
		cf delete-service-key tanf-uaa-client tanf-service-key -f
		cf create-service-key tanf-uaa-client tanf-service-key -c "{\"redirect_uri\": [\"https://$ROUTE/auth/callback\", \"https://$ROUTE/logout\"]}"
		cf set-env tanf UAA_CLIENT_ID $(cf service-key tanf-uaa-client tanf-service-key | grep client_id | awk '{print $2}' | sed 's/^"\(.*\)",*$/\1/')
		cf set-env tanf UAA_CLIENT_SECRET $(cf service-key tanf-uaa-client tanf-service-key | grep client_secret | awk '{print $2}' | sed 's/^"\(.*\)",*$/\1/')
		cf restart tanf
	fi
fi


# tell people where to go
echo
echo
echo "to log into the site, you will want to go to https://${ROUTE}/"
echo 'Have fun!'
