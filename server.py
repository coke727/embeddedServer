#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import ssl
from os import curdir, sep, system, stat
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys
import re
import base64
import subprocess
import hashlib
from subprocess import PIPE
import Cookie
import errno
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from crontab import CronTab
from crontabs import CronTabs
from os import listdir
from os.path import isfile, join

PORT_NUMBER = 80
configuration_path = "./html/configuration.html"
samples_show = 20
scp_adress = ""
scp_frequency = 0
store_data = False
frequency = 0
cookies = []
samples_path ="./data/"

#This class will handles any incoming request from the browser 
class myHandler(BaseHTTPRequestHandler):

	@staticmethod
	def isInt(s):
		try: 
			int(s)
			return True
		except ValueError:
			return False

	# Simplify the intervals array returning a new array simplified.
	def remove_overlap(self, intervals): #sol by http://www.geeksforgeeks.org/merging-intervals/
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
	def getIntervalArray(self, intervals):
		regex = re.compile("\(\d+,\d+\)")
		result = []
		for match in regex.finditer(intervals):
			interval = eval(match.group(0))
			if( interval[0] < interval[1] and interval[0] >= 0 and interval[1] >= 1):
				result.append(interval)
		return result

	def getSamples(n):
		with open("data/samples.txt") as myfile:
			head = [next(myfile) for x in xrange(n)]
		print head

	def create_empty(self):
		with open("html/web.html",'w+') as new_file:
			with open("html/empty_web.html") as old_file:
				for line in old_file:
					new_file.write(line)

	def create_web(self, num_samples):
		datafiles = [f for f in listdir(samples_path) if isfile(join(samples_path, f))]
		datafiles.sort(reverse=True)
		
		with open("html/web.html",'w+') as new_file:
			with open("html/web_bone.html") as old_file:
				for line in old_file:
					new_file.write(line)
			try:
				if stat(samples_path+datafiles[0]).st_size == 0:
					old_file.close()
					new_file.close()
					self.create_empty()
				else:
					samples_added = 0
					file_index = 0
					while samples_added < num_samples:
						with open(samples_path+datafiles[file_index]) as samples:
							for i, line in enumerate(samples):
								tupla = [x.strip() for x in line.split(';')]
								new_file.write("<tr><td>" + tupla[0] + "</td><td>" + tupla[1] + "</td></tr>")
								samples_added+=1
								if samples_added == num_samples:
									break
						samples.close()
						file_index+=1
						if(file_index >= len(datafiles)):
							break

					new_file.write("</table></article></body></html>")
			except:
				old_file.close()
				new_file.close()
				self.create_empty()
		old_file.close()

	#Check if cookie is stored in server.
	#TODO comprobar que se eliminan correctamente.
	def check_cookie( self, cookie ):
		global cookies
		for c in cookies:
			if(c[0]["cookietemp"].value == cookie["cookietemp"].value):
				return True
			else: #Check if cookie is alive
				if( c[1] < datetime.now()):
					cookies.remove(c)
		return False

	#Store cookie in server when a correct login is perform.
	def store_cookie( self, cookie ):
		global cookies
		cookies.append(( cookie, datetime.now() + timedelta(0, int(cookie['cookietemp']['expires']))))

	#Login validation.
	def check_login( self, login, password ):
		try:
			with open("login.txt", 'r') as file:
				login_hash = file.readline().strip()
				password_hash = file.readline().strip()
			file.close()
			if(login_hash == hashlib.sha256(login).hexdigest() and password_hash == hashlib.sha256(password).hexdigest()):
				return True
			else:
				return False
		except:
			return False

	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			self.create_web(samples_show)
			self.path="html/web.html"
		if self.path=="/configuration":
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				if(self.check_cookie(c)):
					self.path = configuration_path
				else:
					self.path = "html/login.html"
			else:
				self.path="html/login.html"
		if self.path=="/login":
			self.path="html/login.html"

		try:
			#Check the file extension required and
			#set the right mime type

			sendReply = False
			if self.path.endswith(".html"):
				mimetype='text/html'
				sendReply = True
			if self.path.endswith(".js"):
				mimetype='application/javascript'
				sendReply = True
			if self.path.endswith(".css"):
				mimetype='text/css'
				sendReply = True

			if sendReply == True:
				#Open the static file requested and send it
				f = open(curdir + sep + self.path) 
				self.send_response(200)
				self.send_header('Content-type',mimetype)
				self.end_headers()
				self.wfile.write(f.read())
				f.close()
			return


		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)

	def do_POST(self):
		global configuration_path

		if(self.path == '/login'):
			print "[Login Post]"
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})
			
			login = form["login"].value.strip()
			password = form["password"].value.strip()

			if(self.check_login(login, password)):
				#Cookie creation
				c = Cookie.SimpleCookie()
				hash_object = hashlib.md5(str(datetime.now()).encode())
				c['cookietemp'] = str(hash_object.hexdigest())
				c['cookietemp']['domain'] = "localhost"
				c['cookietemp']['expires'] = 1200
				c['cookietemp']['path'] = "/"
				c['cookietemp']['httponly'] = "true"
				self.store_cookie(c)

				self.send_response(200)
				self.send_header('Content-type','text/html')
				self.send_header('Set-Cookie', c.output(attrs=['path', 'expires'], header="Cookie:"))
				
				self.end_headers()
				f = open(curdir + sep + "html/configuration.html")
			else:
				self.send_header('Content-type','text/html')
				self.send_response(403)
				self.end_headers()
				f = open(curdir + sep + "html/login-fail.html")

			self.wfile.write(f.read())
			f.close()

		if(self.path == '/configuration'):
			global samples_show
			global frequency
			isDataCorrect = True

			print "[Configuration Post]"
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			#Session check
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				print "cookie recibida: " + c['cookietemp'].value
				#Cookie validation
				if(self.check_cookie(c)):
					#Data validation
					if not re.match("^[0-9]+$", form["samples"].value):
						self.send_response(402)
						self.end_headers()
					elif not re.match("^[0-9]+$", form["frequency"].value):
						self.send_response(402)
						self.end_headers()
					else:
						if( self.isInt( form["samples"].value ) and int( form["samples"].value ) > 0 ):
							samples_show = int(form["samples"].value)
						else:
							isDataCorrect = False

						if( self.isInt( form["frequency"].value ) and int( form["frequency"].value ) > 0 ):
							frequency = int(form["frequency"].value)
							system("python tempdaemon.py restart " + str(frequency))
						else:
							isDataCorrect = False

						if( isDataCorrect ):
							f = open(curdir + sep + "html/configuration-changed.html")
							self.send_response(200)
						else:
							f = open(curdir + sep + "html/configuration-fail.html")
							self.send_response(402)

						self.send_header('Content-type','text/html')
						self.end_headers()
						self.wfile.write(f.read())
						f.close()
				else:
					self.send_response(403)
					self.end_headers()
			else:
				self.send_response(403)
				self.end_headers()


		if(self.path == '/scp'):
			#Session check
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				print "cookie recibida: " + c['cookietemp'].value
				#Cookie validation
				if(self.check_cookie(c)):
					global store_data
					isDataCorrect = False

					print "[SCP Post]"
					form = cgi.FieldStorage(
						fp=self.rfile,
						headers=self.headers,
						environ={'REQUEST_METHOD':'POST',
								'CONTENT_TYPE':self.headers['Content-Type'],
								})

					if 'check' in form:
						store_data = True
					else:
						store_data = False

					#Data validation
					if self.isInt(form["scpfrequency"].value) and self.isInt(form["port"].value) and form["scp"].value and form["user"].value and form["directory"].value and form["password"].value:
						isDataCorrect = True

					#Store data if user wants.
					if store_data:
						with file("./scp.txt",'w+') as scpfile:
							scpfile.write(form["user"].value+"\n")
							scpfile.write(form["scp"].value+"\n")
							scpfile.write(form["directory"].value+"\n")
							scpfile.write(form["port"].value+"\n")
							scpfile.write(form["password"].value+"\n")
							scpfile.write(form["scpfrequency"].value+"\n")
						scpfile.close()

					#Create scp task.
					#TODO encriptar datos que se pasan al script (?)
					p = subprocess.Popen(["python", "scpdaemon.py", "restart", form["scpfrequency"].value, form["scp"].value, form["user"].value, form["port"].value, form["directory"].value], stdin=PIPE, stdout=PIPE)
					print p.communicate(form["password"].value)
					#TODO check that is correct, subprocess.check~

					#Redirect to configuration.
					if( isDataCorrect ):
						f = open(curdir + sep + "html/configuration-changed.html") 
						self.send_response(200)
					else:
						f = open(curdir + sep + "html/configuration-fail.html") 
						self.send_response(402)

					self.send_header('Content-type','text/html')
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
				else:
					self.send_response(403)
					self.end_headers()
			else:
				self.send_response(403)
				self.end_headers()

		if(self.path == '/pmnormal'):
			#Session check
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				print "cookie recibida: " + c['cookietemp'].value
				#Cookie validation
				if(self.check_cookie(c)):
					#TODO eliminar datos de otros modos, overclock etc.
					print "[Power mode normal Post]"
					system("sudo pmnormal")
					configuration_path = './html/configuration_mode0.html'

					cron = CronTab(user='coke')
					cron.remove_all()
					cron.write_to_user( user=True )

					f = open(curdir + sep + "html/configuration-changed.html") 
					self.send_response(200)
					self.send_header('Content-type','text/html')
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
				else:
					self.send_response(403)
					self.end_headers()
			else:
				self.send_response(403)
				self.end_headers()
			
		if(self.path == '/pm1'):
			#Session check
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				print "cookie recibida: " + c['cookietemp'].value
				#Cookie validation
				if(self.check_cookie(c)):
					#TODO pmnormal.sh -> wifi activado, con underclock, eliminar datos que generen los otros modos etc
					print "[Power mode 1 Post]"
					system("sudo pm1")
					configuration_path = './html/configuration_mode1.html'
					
					cron = CronTab(user='coke')
					cron.remove_all()
					cron.write_to_user( user=True )

					f = open(curdir + sep + "html/configuration-changed.html")
					self.send_response(200)
					self.send_header('Content-type','text/html')
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
				else:
					self.send_response(403)
					self.end_headers()
			else:
				self.send_response(403)
				self.end_headers()
		if(self.path == '/pm2_multiple'):
			configuration_path = './html/configuration_mode2.html'
			#TODO elimnar datos de los otros modos
			print "[Power mode 2 Post: Multiple intervals]"
			
			#Post form recover
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			#Parse and validation of the form data.
			monday = self.remove_overlap(self.getIntervalArray(form["monday"].value))
			tuesday = self.remove_overlap(self.getIntervalArray(form["tuesday"].value))
			wednesday = self.remove_overlap(self.getIntervalArray(form["wednesday"].value))
			thursday = self.remove_overlap(self.getIntervalArray(form["thursday"].value))
			friday = self.remove_overlap(self.getIntervalArray(form["friday"].value))
			saturday = self.remove_overlap(self.getIntervalArray(form["saturday"].value))
			sunday = self.remove_overlap(self.getIntervalArray(form["sunday"].value))

			week = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
			week_keys = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
			cron = CronTab(user='coke')
			
			#Create cronjobs for enter in mode 2
			for i, day in enumerate(week):
				job  = cron.new(command='echo hola modo2', comment= 'mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[0][0])
				for interval in day[1:]:
					job.hour.also.on(interval[0])

			#Create cronjobs for exist from mode 2 to the last mode used.
			for i, day in enumerate(week):
				job  = cron.new(command='echo adios modo2', comment= '!mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[0][1])
				for interval in day[1:]:
					job.hour.also.on(interval[1])

			#Write crontab in a file and in system cron table.
			cron.write( './crons/mp2.tab' )
			cron.write_to_user( user=True )

			f = open(curdir + sep + "html/configuration-changed.html")
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		if(self.path == '/pm2_one'):
			configuration_path = './html/configuration_mode2.html'
			print "[Power mode 2 Post: One interval]"

			#Post form recover
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			monday = tuesday = wednesday = thursday = friday = saturday = sunday = (int(form["start"].value),int(form["end"].value))

			week = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
			week_keys = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
			cron = CronTab(user='coke')

			#Create cronjobs for enter in mode 2
			for i, day in enumerate(week):
				job  = cron.new(command='echo hola modo2', comment= 'mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[0])

			#Create cronjobs for exist from mode 2 to the last mode used.
			for i, day in enumerate(week):
				job  = cron.new(command='echo adios modo2', comment= '!mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[1])

			#Write crontab in a file and in system cron table.
			cron.write( './crons/mp2.tab' )
			cron.write_to_user( user=True )

			f = open(curdir + sep + "html/configuration-changed.html") 
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()

		if(self.path == '/pm2_eachday'):
			configuration_path = './html/configuration_mode2.html'
			print "[Power mode 2 Post: Multiple intervals]"

			#Post form recover
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			#Parse and validation of the form data.
			monday = (int(form["monday_start"].value), int(form["monday_end"].value))
			tuesday = (int(form["tuesday_start"].value), int(form["tuesday_end"].value))
			wednesday = (int(form["wednesday_start"].value), int(form["wednesday_end"].value))
			thursday = (int(form["thursday_start"].value), int(form["thursday_end"].value))
			friday = (int(form["friday_start"].value), int(form["friday_end"].value))
			saturday = (int(form["saturday_start"].value), int(form["saturday_end"].value))
			sunday = (int(form["sunday_start"].value), int(form["sunday_end"].value))

			week = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
			week_keys = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
			cron = CronTab(user='coke')

			#Create cronjobs for enter in mode 2
			for i, day in enumerate(week):
				job  = cron.new(command='echo hola modo2', comment= 'mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[0])

			#Create cronjobs for exist from mode 2 to the last mode used.
			for i, day in enumerate(week):
				job  = cron.new(command='echo adios modo2', comment= '!mp2 '+week_keys[i])
				job.dow.on(week_keys[i])
				job.hour.on(day[1])

			#Write crontab in a file and in system cron table.
			cron.write( './crons/mp2.tab' )
			cron.write_to_user( user=True )

			f = open(curdir + sep + "html/configuration-changed.html") 
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()
		if(self.path == '/pm3'):
			configuration_path = './html/configuration_mode3.html'
			print "[Power mode 3 Post]"
			#TODO modo 3 -> pmsleep.sh -> depender del RTC para encender raspi antes de cada medida o en la fecha pedida por el usuario
			#hay que eliminar los datos generados por los otros modos y generar los datos necesarios.
try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER

	#httpd = BaseHTTPServer.HTTPServer(('localhost', 4443), myHandler)
	#httpd.socket = ssl.wrap_socket (httpd.socket, certfile='path/to/localhost.pem', server_side=True)
	#httpd.serve_forever()
	
	#Wait forever for incoming http requests
	server.serve_forever()

except KeyboardInterrupt:
	#TODO cerrar daemon (?)
	print '^C received, shutting down the web server'
	server.socket.close()
