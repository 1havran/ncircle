use warnings;						# warnings
use strict;							# strict checking
use ParApi::ApiClient;				# tpam api
use RPC::XML::Client;				# xml lib for ncircle

my $id;								# used for password request handling between called methods
my $client;							# it handles connection to the TPAM & nCircle server
my $verbose = 1;					# for debug purposes (0, 1, 2)

my $tpamHost = "192.168.1.1";		# ip address of TPAM appliance where API is allowed. via tcp/22 - ssh
my $tpamApiUserName = "PERL_API";	# username to login to TPAM via api
my $tpamKeyFileName = "id_dsa";		# id_dsa key generated for apiUserName from TPAM WEB

my $tpamSystemName = "API_Test";	# system name to which password is being requested
my $tpamAccountName = "Perl_API";	# system user name to which password is being requested
my $tpamRequestNotes = "PERL_API";	# notes for password request in TPAM

my $nCircleHost = 'https://192.168.1.2/api2xmlrpc';	# url for nCircle APIv2
my $nCircleUser = 'ip360@ncircle.com';					# username for login to api
my $nCirclePassword = 'password';					# password for login to api
my $nCircleUserID = 'User.3';							# user id of username to which the password is being changed

# we create new password request for the pair of $systemName and $accountName. 
    sub addPwdRequest {
        my ($rc, $id, $msg) = $client->addPwdRequest(
          systemName   => $tpamSystemName,
          accountName  => $tpamAccountName,
		  requestNotes => $tpamRequestNotes);
                                           
        if ($rc == 0) {
           print "addPwdRequest: ok: $rc\n $id\n $msg\n" if ($verbose == 2);		   
        } else {
           print "addPwdRequest: error: $rc\n$id\n$msg\n" if ($verbose == 2);
        }
		return $id;	# return ID of the request
    }                          

# retrieve password from the password request. 
# requestID number is taking as a first argument
	sub retrieve {		
		my $id = shift;
		print "retrieve: info: id is: $id\n" if ($verbose == 2);
        my ($rc, $msg) = $client->retrieve(requestID => "$id");                                            
		if ($rc == 0) {
           print "retrieve: ok: $msg\n" if ($verbose == 2);
		   return $msg;
		} else {
           print "retrieve: error: $msg\n" if ($verbose == 2);
		}
	} 

# get ID of actual password request	
	sub listAcctsForPwdRequest {		
        my ($rc, $count, $msg, @list) = $client->listAcctsForPwdRequest(
		  systemName => $tpamSystemName, accountName  => $tpamAccountName);                                        
		if ($rc == 0) {	#currently there should be just one request at the moment, but in the future we should return list of $id's and each should be individually processed
			for (my $i=0; $i<$count; $i++) {
				my $id = ${$list[$i]}{'reqID'};
				return $id
			}		   
		} else {
           print "listRequest: error: $msg\n" if ($verbose == 2);
		   return 0;
		}
	}

	
print "\n$0 - password request via TPAM and change it in nCircle\n" if $verbose;
print "---------------------------------------------------------\n" if $verbose;
	
# create connection to TPAM	
$client = ParApi::ApiClient->new(host => $tpamHost, keyFileName => $tpamKeyFileName, userName => $tpamApiUserName);
$client->setCommandTimeout(120);  # set SSH timeout to 120 seconds

# get actual ID
print "$0: tpam: get actual requests ... " if $verbose;
$id = listAcctsForPwdRequest;
print "done\n" if $verbose;
print $id if ($verbose == 2);

# if request does not exist, create new one
print "$0: tpam: get pwd requests for system $tpamSystemName and user $tpamAccountName... " if $verbose;
$id = addPwdRequest if not ($id);
print "done\n" if $verbose;

# retrieve password. display it on the stdout
print "$0: tpam: retrieve password ... " if $verbose;
my $password = retrieve($id);
print "done\n" if $verbose;

# connect to nCircle and update the relevant username with the new password
if ($password) {	
	# update password in nCircle
	$client = RPC::XML::Client->new($nCircleHost);
	print "$0: ncircle: login ... " if $verbose;
	my $cookie = $client->simple_request('login', 2, 0,$nCircleUser, $nCirclePassword);
	print "done\n" if $verbose;
	
	print "$0: ncircle: password changing for user $nCircleUserID ... " if $verbose;
	my $result = $client->simple_request('call', $cookie, $nCircleUserID,'setPassword', {password => $password});
	print "done\n" if $verbose;
	
} else {
	print "$0: error: failed to receive password from TPAM!\n" if $verbose;
}
