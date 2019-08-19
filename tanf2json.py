#!/usr/bin/env python3
# 
# This script parses the txt files that are sent by STT people to the TDRS
# app and emits a json document.  The data format is documented here:  
# https://www.acf.hhs.gov/ofa/resource/tanfedit/index#transmission-file-header
# The fields are defined with the various *_fields dictionaries.
# The keys are the json names for the fields, and the values are the size of
# the fields in bytes.
#
# Possible tricky bits:  
#  1) We do not parse the fields at all, but just pull them
#     in as strings.  So we don't do any type parsing or anything.  That might
#     better be done by code that consumes the json doc and stores it.
#  2) The social security numbers have dashes put into them, which may not
#     be the way they are parsed/stored in the existing system.
# 
# This script must be run with python 3.6 or above, because it preserves
# the order of dictionaries, which we need for this to work.
#
# usage:  python3 tanf2json.py sec1_encr_fake.txt > /tmp/sec1_encr_fake.json
#
# XXX The fields here for the family/adult/child records are incomplete,
#     and only section 1 has been stubbed out.  More work is required to
#     make this parse all record types and all sections.
#

import sys
import json
import struct
import collections
import sys
import re

header_fields = {
	"title": 6,
	"calendarquarter": 5,
	"datatype": 1,
	"statefipscode": 2,
	"tribecode": 3,
	"programtype": 3,
	"editindicator": 1,
	"encryptionindicator": 1,
	"updateindicator": 1
}

section1_familydata_fields = {
	"recordtype": 2,
	"reportingmonth": 6,
	"casenumber": 11,
	"countyfipscode": 3,
	"stratum": 2,
	"zipcode": 5,
	"fundingstream": 1,
	"disposition": 1,
	"newapplicant": 1,
	"numfamilymembers": 2,
	"typeoffamilyforworkparticipation": 1,
	"receivessubsidizedhousing": 1,
	"receivesmedicalassistance": 1,
	"receivesfoodstamps": 1,
	"amtoffoodstampassistance": 4,
	"receivessubsidizedchildcare": 1,
	"amtofsubsidizedchildcare": 4,
	"amtofchildsupport": 4,
	"amtoffamilycashresources": 4,
	"cash_item21a_amount": 4,
	"cash_item21b_nbr_month": 3,
	"tanfchildcare_item22a_amount": 4,
	"tanfchildcare_item22b_children_covered": 2,
	"tanfchildcare_item22c_nbr_months": 3,
	"transportation_item23a_amount": 4,
	"transportation_item23b_nbr_months": 3,
	"transitionalservices_item24a_amount": 4,
	"transitionalservices_item24b_nbr_months": 3,
	"other_item25a_amount": 4,
	"other_item25b_nbr_months": 3,
	"reasonforandamtofassistancereduction_item26a_sanctionsreduction_amt": 4,
	"reasonforandamtofassistancereduction_item26a_workrequirementssanction": 1,
	"reasonforandamtofassistancereduction_item26a_familysanctionforadultnohsdiploma": 1,
	"reasonforandamtofassistancereduction_item26a_sanctionforteenparentnotattendingschool": 1,
	"reasonforandamtofassistancereduction_item26a_noncooperatewithchildsupport": 1,
	"reasonforandamtofassistancereduction_item26a_failuretocomploywithirp": 1,
	"reasonforandamtofassistancereduction_item26a_othersanction": 1,
	"reasonforandamtofassistancereduction_item26b_recoupmentofprioroverpayment": 4,
	"reasonforandamtofassistancereduction_item26c_othertotalreductionamt": 4,
	"reasonforandamtofassistancereduction_item26c_familycap": 1,
	"reasonforandamtofassistancereduction_item26c_reductionbasedonlengthofreceiptofassistance": 1,
	"reasonforandamtofassistancereduction_item26c_othernonsanction": 1,
	"waiver_evaluation_control_gprs": 1,
	"tanffamilyexemptfromtimelimits": 2,
	"tanffamilynewchildonlyfamily": 1,
	"blank": 39
}

section1_adultdata_fields = {
	"recordtype": 2,
	"reportingmonth": 6,
	"casenumber": 11,
	"familyafilliation": 1,
	"noncustodialparent": 1,
	"dateofbirth": 8,
	"socialsecuritynumber": 9,
	"racehispanic": 1,
	"racenativeamerican": 1
}

section1_childdata_fields = {
	"recordtype": 2,
	"reportingmonth": 6,
	"casenumber": 11,
	"familyafilliation": 1,
	"dateofbirth": 8,
	"socialsecuritynumber": 9,
	"racehispanic": 1,
	"racenativeamerican": 1
}

trailer_fields = {
	"title": 7,
	"numrecords": 7,
	"blank": 9
}

def parseFields(fieldinfo, linestring):
	fields = list(fieldinfo.keys())
	fieldwidths = list(fieldinfo.values())
	fmtstring = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's')
    	                    for fw in fieldwidths)
	fieldstruct = struct.Struct(fmtstring)
	unpack = fieldstruct.unpack_from
	parse = lambda line: tuple(s.decode() for s in unpack(line.encode()))

	return dict(zip(fields,parse(linestring)))


# This is the simple subtitution cipher
encryptmap = {
	'1': '@',
	'2': '9',
	'3': 'Z',
	'4': 'P',
	'5': '0',
	'6': '#',
	'7': 'Y',
	'8': 'B',
	'9': 'W',
	'0': 'T',
}
decryptmap = {}
for k,v in encryptmap.items():
	decryptmap[v] = k

# This decrypts the ssn using the silly substitution cipher
def decryptSsn(ssn):
	result = ''
	for z in ssn:
		try:
			result = result + decryptmap[z]
		except:
			result = result + z
	if len(result) == 9:
		result = result[:5] + '-' + result[5:]
		result = result[:3] + '-' + result[3:]
	return result


# This is the TANF data structure which we fill up with data and convert into
# json at the end.
tanfdata = {
	'header': {},
	'section1_familydata': [],
	'section1_adultdata': [],
	'section1_childdata': [],
	'trailer': ()
}


# Read the file given on the commandline, parse the different line types.
with open ( sys.argv[1], "r") as f:
	for line in f:
		if re.match(r'^T1', line):
			tanfdata['section1_familydata'].append(parseFields(section1_familydata_fields, line))

		elif re.match(r'^T2', line):
			adult = parseFields(section1_adultdata_fields, line)
			if tanfdata['header']['encryptionindicator'] == 'E':
				adult['socialsecuritynumber'] = decryptSsn(adult['socialsecuritynumber'])
			tanfdata['section1_adultdata'].append(adult)

		elif re.match(r'^T3', line):
			child = parseFields(section1_childdata_fields, line)
			if tanfdata['header']['encryptionindicator'] == 'E':
				child['socialsecuritynumber'] = decryptSsn(child['socialsecuritynumber'])
			tanfdata['section1_childdata'].append(child)

		elif re.match(r'^HEADER', line):
			tanfdata['header'] = parseFields(header_fields, line)

		elif re.match(r'^TRAILER', line):
			tanfdata['trailer'] = parseFields(trailer_fields, line)

		else:
			print('could not figure out record type: ', line)

print(json.dumps(tanfdata))
