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
	  else
	    cf create-service aws-rds shared-psql tanf-db
	  fi
	  echo sleeping until db is awake
	  for i in 1 2 3 ; do
	  	sleep 60
	  	echo $i minutes...
	  done
	fi

	if cf e | grep -q JWT_KEY ; then
		echo jwt cert already created
	else
		generate_jwt_cert
	fi
fi

generate_jwt_cert() 
{
	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -sha256
	cf set-env tanf JWT_CERT "$(cat cert.pem)"
	cf set-env tanf JWT_KEY "$(cat key.pem)"
}

# regenerate jwt cert
if [ "$1" = "regenjwt" ] ; then
	generate_jwt_cert
fi

# launch the app
if [ "$1" = "zdt" ] ; then
	if cf plugins | grep blue-green-deploy >/dev/null ; then
		echo blue-green-deploy plugin already installed
	else
		cf add-plugin-repo CF-Community https://plugins.cloudfoundry.org
		cf install-plugin blue-green-deploy -r CF-Community -f
	fi

	# Do a zero downtime deploy.  This requires enough memory for
	# two tanf apps to exist in the org/space at one time.
    cf blue-green-deploy scanner-ui -f manifest.yml --delete-old-apps || exit 1
else
	cf push || exit 1
fi

# do db migrations if requested
if [ "$1" = "updatedb" ] ; then
	cf run-task tanf "python manage.py migrate" --name migrate
fi

# tell people where to go
ROUTE="$(cf apps | grep tanf | awk '{print $6}')"
echo
echo
echo "to log into the site, you will want to go to https://${ROUTE}/"
echo 'Have fun!'
