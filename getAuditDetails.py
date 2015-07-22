# 20150709: get audit records from nCircle
# - we need to have list of deviceProfilers defined from which the audit records will be fetched
# - max IDs are fetched from audit_file to fetch only latest audit records for each profiler


import xmlrpclib
import sys
import os
import json

# nCircle Variables
host = 'https://192.168.2.1/api2xmlrpc'
user = 'ip360@ncircle.com'
password = 'password'
audit_file = 'audit.json'
blg = 5000

deviceProfilers = ['DP.9','DP.10','DP.11','DP.13','DP.23','DP.25','DP.26','DP.27','DP.28','DP.29','DP.33','DP.35']
#deviceProfilers = ['DP.9']


# Internal dicts
storedAuditIDs = {}
vulnList = {}
hostList = {}
osList = {}

# Get Item from the server, all attributes - no filtering
def _getItem(list,item):
	if not list.get(item):
		list[item] = server.call(session, item, 'getAttributes', {})
	return list[item]
	
# Print dict output, filter out non printable characters	
def _printJson(output):
	for name,data in output.items():
	
		if type(data) == unicode or type(data) == str:
			data = data.encode('ascii','ignore')
		data = str(data).replace('\n', ':')
		
		print "\"%s\": \"%s\"," % (name, data),


# Get the latest Audit IDs for each device profiler
try:
	f = open(audit_file,"r")
	data = f.readline()
	storedAuditIDs = json.loads(data)
	f.close()	
except:
	# Maybe we dont need to exit(1). If file does not exist, we will create it at the and and we will fetch results just > bulgarian constant
	print "Error: Cannot read audit file or wrong json structure!"
	sys.exit(1)
	

# Get the audit records
try:
	# Connect to the server and login
	server = xmlrpclib.ServerProxy(host)
	session = server.login(2, 0, user, password)

	# Find new audits for each device profilers
	for deviceProfiler in deviceProfilers:
	
		#get latest AuditID into the condition for fetching the audit records
		if not storedAuditIDs.get(deviceProfiler):			
			storedAuditIDs[deviceProfiler] = blg	#bulgarian constant to get audits from ID 5000
		else:
			storedAuditID = storedAuditIDs[deviceProfiler]
			
		params = {}
		params['query'] = "id>%s AND dp=\'%s\'" % (storedAuditID, deviceProfiler)
		
		# Audit results are stored under IDs
		auditResultIDs = server.call(session, 'class.Audit', 'search', params)
		if auditResultIDs:
			for auditResultID in auditResultIDs:
	
				# Store max audit ID for future - fetch only new records in next run
				if auditResultID.split(".")[1] > storedAuditIDs[deviceProfiler]:
					storedAuditIDs[deviceProfiler] = auditResultID.split(".")[1]
						
				params = {}
				params['query'] = "audit=\'%s\'" % (auditResultID)
				
				# Vulnerabilities for particular hosts are stored under VulnResult IDs
				vulnResultIDs = server.call(session, 'class.VulnResult', 'search', params)
							
				if vulnResultIDs:
					for vulnResultID in vulnResultIDs:
					
						vulnResult = {}
						vulnDetail = {}
						hostDetail = {}
						osDetail = {}
						
						vulnResult = server.call(session, vulnResultID, 'getAttributes', {})
						
						# Get additional details that are being referenced in the vulnResult
						vulnDetail = _getItem(vulnList, vulnResult['vuln'])
						hostDetail = _getItem(hostList, vulnResult['host'])
						osDetail = _getItem(osList, hostDetail['os'])

						print "{",
						_printJson(vulnResult)
						
						print '"VulnDetail" : {',
						_printJson(vulnDetail)
						print "},",
						
						print '"hostDetail" : {',
						_printJson(hostDetail)
						print "},",
						
						print '"osDetail" : {',
						_printJson(osDetail)
						print "}",
						
						print "}"

	# Logout from server
	server.logout(session)
	

except xmlrpclib.Fault, fault:
	print "xmlrpclib fault: %d %s" % (fault.faultCode, fault.faultString)
	sys.exit(1)
except xmlrpclib.ProtocolError, error:
	print "xmlrpclib protocol error: %d %s" % (error.errcode, error.errmsg)
	sys.exit(1)

	
# Store the latest Audit IDs for each device profiler
try:
	os.remove(audit_file)
	f = open(audit_file,"w")
	data = json.dumps(storedAuditIDs)
	f.write(data)
	f.close()	
except:
	print "Error: Cannot write audit file or wrong json structure!"
	sys.exit(1)	
	
# Exit
sys.exit(0)
