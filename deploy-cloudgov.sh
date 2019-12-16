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
		  echo sleeping until db is awake
		  for i in 1 2 3 ; do
		  	sleep 60
		  	echo $i minutes...
		  done
	  else
	    cf create-service aws-rds shared-psql tanf-db
	    sleep 2
	  fi
	fi

	if cf e tanf | grep -q JWT_KEY ; then
		echo jwt cert already created
	else
		export SETUPJWT="True"
	fi
fi

generate_jwt_cert() 
{
	echo "regenerating JWT cert/key"
	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -sha256
	cf set-env tanf JWT_CERT "$(cat cert.pem)"
	cf set-env tanf JWT_KEY "$(cat key.pem)"

	# make sure that we have something set that you can later override with the
	# proper value so that the app can start up
	if cf e tanf | grep -q OIDC_RP_CLIENT_ID ; then
		echo OIDC_RP_CLIENT_ID already set up
	else
		echo "once you have gotten your client ID set up with login.gov, you will need to set the OIDC_RP_CLIENT_ID to the proper value"
		echo "you can do this by running: cf set-env tanf OIDC_RP_CLIENT_ID 'your_client_id'"
		echo "login.gov will need this cert when you are creating the app:"
		cat cert.pem
		cf set-env tanf OIDC_RP_CLIENT_ID "XXX"
	fi
}


# regenerate jwt cert
if [ "$1" = "regenjwt" ] ; then
	generate_jwt_cert
fi

# launch the app
if [ "$1" = "zdt" ] ; then
	# Do a zero downtime deploy.  This requires enough memory for
	# two apps to exist in the org/space at one time.
	cf v3-zdt-push tanf || exit 1
else
	cf v3-push tanf

	# we have to do this after the tanf app is deployed
	if [ -n "$SETUPJWT" ] ; then
		generate_jwt_cert
		cf restart tanf
	fi
fi

# create a superuser if requested
if [ "$1" = "createsuperuser" ] && [ -n "$2" ] ; then
	cf run-task tanf "python manage.py createsuperuser --email $2 --noinput" --name createsuperuser
fi

# tell people where to go
ROUTE="$(cf apps | grep tanf | awk '{print $6}')"
echo
echo
echo "to log into the site, you will want to go to https://${ROUTE}/"
echo 'Have fun!'
