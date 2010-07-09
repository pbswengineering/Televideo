#
# Regular cron jobs for the televideo package
#
0 4	* * *	root	[ -x /usr/bin/televideo_maintenance ] && /usr/bin/televideo_maintenance
