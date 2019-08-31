#!/bin/sh
#
# This script will attempt to create the services required
# and then launch everything.
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
	# XXX right now, this seems to fail.  Not sure why.
	cf v3-zdt-push tanf || exit 1
else
	cf push || exit 1
fi

# do db migrations if requested
if [ "$1" = "dbsetup" ] ; then
	cf run-task tanf "python manage.py migrate" --name dbsetup
fi

# set up OIDC stuff
ROUTE="$(cf apps | grep tanf | awk '{print $6}')"
if cf service-keys tanf-uaa-client | grep tanf-service-key ; then
	echo OIDC already set up
else
	if [ -z "$ROUTE" ] ; then
		echo "cannot create OIDC service key until the app has been created."
		echo "Get the app running and then re-run the setup"
	else
		cf create-service-key tanf-uaa-client tanf-service-key -c "{\"redirect_uri\": [\"https://$ROUTE/oidc/callback/\", \"https://$ROUTE/logout\"]}"
		cf set-env tanf OIDC_RP_CLIENT_ID $(cf service-key tanf-uaa-client tanf-service-key | grep client_id | awk '{print $2}' | sed 's/^"\(.*\)",*$/\1/')
		cf set-env tanf OIDC_RP_CLIENT_SECRET $(cf service-key tanf-uaa-client tanf-service-key | grep client_secret | awk '{print $2}' | sed 's/^"\(.*\)",*$/\1/')
		cf restart tanf
	fi
fi



# tell people where to go
echo
echo
echo "to log into the site, you will want to go to https://${ROUTE}/"
echo 'Have fun!'
