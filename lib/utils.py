import re
import hashlib
from crontab import CronTab
from crontabs import CronTabs

crontab_user = 'coke'
week_keys = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
week_starts = ['monday_start', 'tuesday_start', 'wednesday_start', 'thursday_start', 'friday_start', 'saturday_start', 'sunday_start']
week_ends = ['monday_end', 'tuesday_end', 'wednesday_end', 'thursday_end', 'friday_end', 'saturday_end', 'sunday_end']
week_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

# Simplify the intervals array returning a new array simplified.
def remove_overlap( intervals ): #sol by http://www.geeksforgeeks.org/merging-intervals/
	sorted_by_lower_bound = sorted(intervals, key=lambda tup: tup[0])
	merged = []

	for higher in sorted_by_lower_bound:
		if not merged:
			merged.append(higher)
		else:
			lower = merged[-1]
			# test for intersection between lower and higher:
			# we know via sorting that lower[0] <= higher[0]
			if higher[0] <= lower[1]:
				upper_bound = max(lower[1], higher[1])
				merged[-1] = (lower[0], upper_bound)  # replace by merged interval
			else:
				merged.append(higher)
	return merged

# Parse a string representation of an interval array toa  real interval array.
def getIntervalArray( intervals ):
	regex = re.compile("\(\d+,\d+\)")
	result = []
	for match in regex.finditer(intervals):
		interval = eval(match.group(0))
		if( interval[0] < interval[1] and interval[0] >= 0 and interval[1] >= 1):
			result.append(interval)
	return result

def isInt(s):
	try: 
		int(s)
		return True
	except ValueError:
		return False

def getConfiguration(config_name):
	value = 0
	try:
		with open("./config/"+config_name, 'r') as file:
			value = file.readline().strip()
		file.close()
		return value
	except:
		return value

def validateInterval(string_start, string_end):
	if(isInt(string_start) and isInt(string_end)):
		start = int(string_start)
		end = int(string_end)
		if start < end and  start > 0 and end < 24 and (start-end) < 23:
			return True
		else:
			return False
	else:
		return False

def validateInterval_eachDay(form):
	week_index = 0
	valid = True
	while week_index < 7:
		if(not validateInterval(form[week_starts[week_index]].value, form[week_ends[week_index]].value)):
			valid = False
		week_index += 1
	return valid

def validateInterval_multiple(form):
	regex = re.compile("(\(\d+,\d+\),)*\(\d+,\d+\)")
	week_index = 0
	valid = True
	while week_index < 7:
		if (not regex.match(form[week_days[week_index]].value)):
			print "false regex.match"
			valid = False
			break
		intervals = remove_overlap(getIntervalArray(form[week_days[week_index]].value))
		total_hours = 0
		for interval in intervals:
			total_hours += (interval[1] - interval[0])
			if interval[0] < 0 or interval[1] > 23:
				valid = False
				break 
		if total_hours >= 23:
			print "> 24h"
			valid = False
			break
		week_index += 1
	return valid

# --------------- #
# Login Functions #
# --------------- #

#Login validation.
def check_login( login, password ):
	try:
		with open("./config/login", 'r') as file:
			login_hash = file.readline().strip()
			password_hash = file.readline().strip()
		file.close()
		if(login_hash == hashlib.sha256(login).hexdigest() and password_hash == hashlib.sha256(password).hexdigest()):
			return True
		else:
			return False
	except:
		return False

# -------------------------- #
# Crontab Creation Functions #
# -------------------------- #

def remove_crontab():
		cron = CronTab(user=crontab_user)
		cron.remove_all()
		cron.write_to_user( user=True )

def create_crontab( form, isAdvanced ):
	#Parse and validation of the form data.
	if(isAdvanced):
		monday = remove_overlap(getIntervalArray(form["monday"].value))
		tuesday = remove_overlap(getIntervalArray(form["tuesday"].value))
		wednesday = remove_overlap(getIntervalArray(form["wednesday"].value))
		thursday = remove_overlap(getIntervalArray(form["thursday"].value))
		friday = remove_overlap(getIntervalArray(form["friday"].value))
		saturday = remove_overlap(getIntervalArray(form["saturday"].value))
		sunday = remove_overlap(getIntervalArray(form["sunday"].value))

		write_crontab([monday,tuesday,wednesday,thursday,friday,saturday,sunday], True)
	else:
		#Parse and validation of the form data.
		monday = (int(form["monday_start"].value), int(form["monday_end"].value))
		tuesday = (int(form["tuesday_start"].value), int(form["tuesday_end"].value))
		wednesday = (int(form["wednesday_start"].value), int(form["wednesday_end"].value))
		thursday = (int(form["thursday_start"].value), int(form["thursday_end"].value))
		friday = (int(form["friday_start"].value), int(form["friday_end"].value))
		saturday = (int(form["saturday_start"].value), int(form["saturday_end"].value))
		sunday = (int(form["sunday_start"].value), int(form["sunday_end"].value))

		write_crontab([monday,tuesday,wednesday,thursday,friday,saturday,sunday], False)


def write_crontab( week, isAdvanced):
	cron = CronTab(user=crontab_user)
	
	if(isAdvanced):
		#Create cronjobs for enter in mode 2
		for i, day in enumerate(week):
			job  = cron.new(command='sudo pm2', comment= 'mp2 '+week_keys[i])
			job.dow.on(week_keys[i])
			job.hour.on(day[0][0])
			for interval in day[1:]:
				job.hour.also.on(interval[0])

		#Create cronjobs for exist from mode 2 to the last mode used.
		for i, day in enumerate(week):
			job  = cron.new(command='sudo pm1', comment= '!mp2 '+week_keys[i])
			job.dow.on(week_keys[i])
			job.hour.on(day[0][1])
			for interval in day[1:]:
				job.hour.also.on(interval[1])
	else:
		#Create cronjobs for enter in mode 2
		for i, day in enumerate(week):
			job  = cron.new(command='sudo pm2', comment= 'mp2 '+week_keys[i])
			job.dow.on(week_keys[i])
			job.hour.on(day[0])

		#Create cronjobs for exist from mode 2 to the last mode used.
		for i, day in enumerate(week):
			job  = cron.new(command='sudo pm1', comment= '!mp2 '+week_keys[i])
			job.dow.on(week_keys[i])
			job.hour.on(day[1])
	#Write crontab in a file and in system cron table.
	cron.write( './crons/mp2.tab' )
	cron.write_to_user( user=True )
