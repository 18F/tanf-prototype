#!/bin/sh
#
# This is what sets up and actually runs the test
#
# You can run it like ./test.sh nodelete to leave the test env running
#

docker-compose down
docker-compose up -d --build

# find the container name:
CONTAINER=$(docker-compose images | awk '/tanf-prototype_tanf/ {print $1}')

# Wait until it is running
echo waiting until "$CONTAINER" is running
until docker ps -f name="$CONTAINER" -f status=running | grep tanf ; do
	docker ps
	sleep 2
done

echo "====================================== Python tests"
docker exec "$CONTAINER" ./manage.py test
PYTESTEXIT=$?


# do an OWASP ZAP scan
docker exec "$CONTAINER" ./manage.py migrate
export ZAP_CONFIG=" \
  -config globalexcludeurl.url_list.url\(0\).regex='.*/robots\.txt.*' \
  -config globalexcludeurl.url_list.url\(0\).description='Exclude robots.txt' \
  -config globalexcludeurl.url_list.url\(0\).enabled=true \
  -config spider.postform=true"

CONTAINER=$(docker-compose images | awk '/zaproxy/ {print $1}')
echo "====================================== OWASP ZAP tests"
docker exec "$CONTAINER" zap-full-scan.py -t http://tanf:8000/about/ -m 5 -z "${ZAP_CONFIG}" | tee /tmp/zap.out 
if grep 'FAIL-NEW: 0' /tmp/zap.out >/dev/null ; then
	ZAPEXIT=0
else
	ZAPEXIT=1
fi


# clean up (if desired)
if [ "$1" != "nodelete" ] ; then
	docker-compose down
fi

echo "====================================== Overall test failures: "
EXIT=0
if [ "$ZAPEXIT" != 0 ] ; then
	echo "OWASP ZAP scan failed"
	EXIT=1
fi

if [ "$PYTESTEXIT" != 0 ] ; then
	echo "Python tests failed"
	EXIT=1
fi

exit $EXIT
