# otodata-genmon
Otodata TM6030 Propane Sensor to Genmon and Hubitat

# Instructions
This assumes you're running genmon. If you're not, you may need to adjust the
final location of where your script will be stored in the .service file. This
also assumes bluetooth is working and can see your Otodata sensor. 

1. Copy otodata_receiver.pl to ~pi/genmon/OtherApps
2. <code>apt-get install libwww-perl</code>
3. Make sure bluetooth is actually enabled, working, and you can see your TM6030 device: <code>sudo hcitool lescan --duplicates </code>
4. If you can, then you're good to proceed. 

5. Go back in otodata_receiver.pl and edit variables. If you're using hubitat,
then you'll need the app & driver from here:
https://github.com/bdwilson/hubitat/tree/master/Otodata-Propane. Add both app
(enable oauth!) and driver, then create a virtual driver and name it whatever you wish. Add the
user app and select this newly-created driver. Get the URL and Key from this
and add it back into otodata_receiver.pl.
6. Make sure the pi user can run things as sudo without a password. Edit
/etc/sudoers to add the following:
<code>
pi ALL = NOPASSWD: /usr/bin/hcitool
</code>
7. <code>sudo cp otodata.service /etc/systemd/system </code>
8. Enable systemd service: <code>sudo systemctl enable otodata</code>
9. Start systemd service: <code>sudo systemctl start otodata</code>
10. Check logs to make sure things are working <code>sudo journalctl -u otodata.service -f (to follow the output)</code>

Bugs/Contact Info
-----------------
Bug me on Twitter at [@brianwilson](http://twitter.com/brianwilson) or email me [here](http://cronological.com/comment.php?ref=bubba).
