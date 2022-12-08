#!/usr/bin/perl
# 
# This is a horrible hacky script, but it gets the job done.
# 
# Install libwww-perl
# $ sudo apt-get install libwww-perl
# 
# You should confirm you can see bluetooth devices:
# $ sudo hcitool lescan
#
# Also, make sure pi user can run hcitool without a password:
# You can add this to /etc/sudoers.
# pi ALL = NOPASSWD: /usr/bin/hcitool
#
# sudo cp otodata.service /etc/systemd/system
# sudo systemctl enable otodata.service
# sudo systemctl start otodata.service
# journalctl -u otodata.service -f (to follow the output) 
#
# Make sure you adjust variables below as needed.
#
use LWP::Simple;

$debug=1;
# do you have genmon running locally?
$doGenmon=1;
# do you want to send data to Hubitat?
$doHubitat=1;
# what is your tank capacity
$capacity="320";
# what are the hubitat URL and key for the app
# https://github.com/bdwilson/hubitat/tree/master/Otodata-Propane
$hubitat_url="http://192.168.1.xx/apps/api/xxx/update/";
$hubitat_key="0940aac2-355b-xxxxx-xxxxxx-xxxxx-xxxx";

### Don't change anything below here.

$genmon_string = '\'generator: set_tank_data={"Tank Name": "External Tank", "Capacity": CAP, "Percentage": PER}\''; 
$| = 1;
open my $fh, '-|', "sudo hcitool lescan --duplicates" or die 'Unable to open';
while (<$fh>) {
	chomp;
	# Complete Local Name: 'level: 56.1 % horiz'
	if (/level\:\s(.*)\s\%/) {
		$level = $1; 
		#print "HERE $1\n";
		if ($level) {
			if (($old_level != $level)) {
				if ($debug) {
					$date=`date`;
					chomp($date);
					print "Date: $date Level: $level\n";
				}
				if ($doGenmon) {
					&do_genmon($level);
				}
				if ($doHubitat) {
					&do_hubitat($level);
				}
			}
			$old_level = $level;
		}
	}
}
close $fh;

sub do_hubitat {
	my $level = shift;
	my $hubitat_out = $hubitat_url . "$level?access_token=" . $hubitat_key; 
	my $out = get($hubitat_out);
	if ($debug) {
		print "HUBITAT: $hubitat_out\n";
		print "RETURN: $out\n";
	}
}
	
sub do_genmon {
	my $level=shift;
	$genmon_out = $genmon_string;
	$genmon_out =~ s/ PER/ $level/;
	$genmon_out =~ s/ CAP/ $capacity/;
	if ($debug) {
		print "DATA: $genmon_out\n";
	}
	open(GENMON, "echo $genmon_out | python3 /home/pi/genmon/ClientInterface.py|");
	while(<GENMON>) {
		if ($debug) {	
			print "GENMON: $_\n";
		}
	}
	close(GENMON)
}
	
