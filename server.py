#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import ssl
from os import curdir, sep, system, stat
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys
import base64
import subprocess
import hashlib
from subprocess import PIPE
import Cookie
import errno
from datetime import datetime
from Crypto.Cipher import AES
from crontab import CronTab
from crontabs import CronTabs
from CookieStorage import CookieStorage
from web_maker import create_empty, create_web
import re
import utils

PORT_NUMBER = 80
configuration_path = "./html/configuration.html"
samples_show = 20
scp_adress = ""
scp_frequency = 0
store_data = False
frequency = 0
cookie_storage = CookieStorage()

#This class will handles any incoming request from the browser 
class myHandler(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			create_web(samples_show)
			self.path="html/web.html"
		if self.path=="/configuration":
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				if(cookie_storage.check_cookie(c)):
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

			if(utils.check_login(login, password)):
				#Cookie creation
				c = Cookie.SimpleCookie()
				hash_object = hashlib.md5(str(datetime.now()).encode())
				c['cookietemp'] = str(hash_object.hexdigest())
				c['cookietemp']['domain'] = "localhost"
				c['cookietemp']['expires'] = 1200
				c['cookietemp']['path'] = "/"
				c['cookietemp']['httponly'] = "true"
				cookie_storage.store_cookie(c)

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
				if(cookie_storage.check_cookie(c)):
					#Data validation
					if not re.match("^[0-9]+$", form["samples"].value):
						self.send_response(402)
						self.end_headers()
					elif not re.match("^[0-9]+$", form["frequency"].value):
						self.send_response(402)
						self.end_headers()
					else:
						if( utils.isInt( form["samples"].value ) and int( form["samples"].value ) > 0 ):
							samples_show = int(form["samples"].value)
						else:
							isDataCorrect = False

						if( utils.isInt( form["frequency"].value ) and int( form["frequency"].value ) > 0 ):
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
				if(cookie_storage.check_cookie(c)):
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
					if utils.isInt(form["scpfrequency"].value) and utils.isInt(form["port"].value) and form["scp"].value and form["user"].value and form["directory"].value and form["password"].value:
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
				if(cookie_storage.check_cookie(c)):
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
				if(cookie_storage.check_cookie(c)):
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
			monday = utils.remove_overlap(utils.getIntervalArray(form["monday"].value))
			tuesday = utils.remove_overlap(utils.getIntervalArray(form["tuesday"].value))
			wednesday = utils.remove_overlap(utils.getIntervalArray(form["wednesday"].value))
			thursday = utils.remove_overlap(utils.getIntervalArray(form["thursday"].value))
			friday = utils.remove_overlap(utils.getIntervalArray(form["friday"].value))
			saturday = utils.remove_overlap(utils.getIntervalArray(form["saturday"].value))
			sunday = utils.remove_overlap(utils.getIntervalArray(form["sunday"].value))

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
