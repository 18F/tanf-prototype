#!/bin/sh
#
# This is what sets up and actually runs the test
#
# You can run it like ./test.sh nodelete to leave the test env running
#

# This eliminates some noise while testing
mkdir -p /tmp/tanf

. ./venv/bin/activate
export JWT_KEY='XXXNOTAKEYXXX'
export NOLOGINGOV=TRUE
export DEBUG=true
export OIDC_RP_CLIENT_ID='urn:gov:gsa:openidconnect.profiles:sp:sso:xxx:xxx'
./manage.py test
