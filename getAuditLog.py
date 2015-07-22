# 20150707: get audit logs from nCircle
# Import the required xmlrpc library
import xmlrpclib
import sys
import os

# nCircle Variables
host = 'https://192.168.2.1/api2xmlrpc'
user = 'ip360@ncircle.com'
password = 'password'
counter_file = 'counter_file.txt'

latest_counter = 188478

# Print dict output, filter out non printable characters	
def _printJson(output):
	for name,data in output.items():
	
		if type(data) == unicode or type(data) == str:
			data = data.encode('ascii','ignore')
		data = str(data).replace('\n', ':')
		
		print "\"%s\": \"%s\"," % (name, data),

		
# Read latest counter for fetching the audit records
try:
	f = open(counter_file,"r+")
	latest_counter = f.readline()
	f.close()
except:
	print "Error: Cannot read counter file!"
	print "Counter taken from default!"
	

# Get the audit records
try:
	# Connect to the server and login
	server = xmlrpclib.ServerProxy(host)
	session = server.login(2, 0, user, password)

	# Construct query to get latest audit records
	result = server.call(session, 'SESSION', 'getUserObject', {})
	params = {}
	params['query'] = "id > \'%s\'" % (latest_counter)
		
	newAuditRecords = server.call(session, 'class.AuditLog', 'search', params)
	if newAuditRecords:
		for newAuditRecord in newAuditRecords:
			result = ''
			result = server.call(session, newAuditRecord, 'getAttributes', {})
			print "{",
			_printJson(result)
			print "}"
			#print result
	
	# Max ID is stored in latest result
	maxId = result['id']
	
	# Safe Logout
	server.logout(session)

except xmlrpclib.Fault, fault:
	print "xmlrpclib fault: %d %s" % (fault.faultCode, fault.faultString)
	sys.exit(1)
except xmlrpclib.ProtocolError, error:
	print "xmlrpclib protocol error: %d %s" % (error.errcode, error.errmsg)
	sys.exit(1)
	
# Store maxID in the file	
try:	
	os.remove(counter_file)
	f = open(counter_file,"w")
	s = str(maxId)
	f.write(s)
	f.close()	
except:
	print "Error: Cannot remove or write file with latest ID for fetching audit records"
	sys.exit(1)
	
# exit
sys.exit(0)
