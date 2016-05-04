#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import ssl
from os import curdir, sep, system, stat
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys
sys.path.append( "./lib" )
import base64
import subprocess
import hashlib
from subprocess import PIPE
import Cookie
import errno
from datetime import datetime
from Crypto.Cipher import AES
from CookieStorage import CookieStorage
from web_maker import create_empty, create_web
import re
import utils
from weatherStation import ip_configuration

PORT_NUMBER = 80
configuration_path = "./html/configuration.html"
samples_show = 20
samples_file = 120
scp_adress = ""
scp_frequency = 0
store_data = False
frequency = 0
cookie_storage = CookieStorage()

#This class will handles any incoming request from the browser 
class myHandler(BaseHTTPRequestHandler):

	def setPowerSavingModeNormal(self):
		global configuration_path
		system("sudo pmnormal")
		configuration_path = './html/configuration.html'
		utils.remove_crontab()

	def setPowerSavingMode1(self):
		global configuration_path
		system("sudo pm1")
		configuration_path = './html/configuration_mode1.html'
		utils.remove_crontab()

	def answerPost(self, path, code):
		f = open(path)
		self.send_response(code)
		self.send_header('Content-type','text/html')
		self.end_headers()
		self.wfile.write(f.read())
		f.close()

	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			create_web(samples_show)
			self.path="html/web.html"
		if self.path=="/configuration":
			if (cookie_storage.check_session(self.headers)):
				self.path = configuration_path
			else:
				self.path = "html/login.html"
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
				self.wfile.write(f.read())
				f.close()
			else:
				self.answerPost(curdir + sep + "html/login-fail.html", 200)

		if(self.path == '/configuration'):
			global samples_show
			global samples_file
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
			if (cookie_storage.check_session(self.headers)):
				#Data validation
				if not re.match("^[0-9]+$", form["samples"].value):
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
				elif not re.match("^[0-9]+$", form["frequency"].value):
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
				elif not re.match("^[0-9]+$", form["websamples"].value):
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
				else:
					if( utils.isInt( form["websamples"].value ) and int( form["websamples"].value ) > 0 ):
						samples_show = int(form["websamples"].value)
						utils.setConfiguration("samples_show" , samples_show)
					else:
						isDataCorrect = False

					if( utils.isInt( form["samples"].value ) and int( form["samples"].value ) > 0 ):
						samples_file = int(form["samples"].value)
						utils.setConfiguration("file_size" , samples_file)
					else:
						isDataCorrect = False

					if( utils.isInt( form["frequency"].value ) and int( form["frequency"].value ) > 0 ):
						frequency = int(form["frequency"].value)
						utils.setConfiguration("frequency_temp" , frequency)
					else:
						isDataCorrect = False

					if( isDataCorrect ):
						self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
					else:
						self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)


		if(self.path == '/scp'):
			#Session check
			if (cookie_storage.check_session(self.headers)):
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

				utils.setConfiguration("frequency_scp", form["scpfrequency"].value)

				#Store data if user wants.
				if store_data:
					with file("./config/scp",'w+') as scpfile:
						scpfile.write(form["user"].value+"\n")
						scpfile.write(form["scp"].value+"\n")
						scpfile.write(form["directory"].value+"\n")
						scpfile.write(form["port"].value+"\n")
						scpfile.write(form["password"].value+"\n")
					scpfile.close()

				#Create scp task.
				#TODO encriptar datos que se pasan al script (?)
				p = subprocess.Popen(["python", "scpdaemon.py", "start", form["scp"].value, form["user"].value, form["port"].value, form["directory"].value], stdin=PIPE, stdout=PIPE)
				print p.communicate(form["password"].value)
				#TODO check that is correct, subprocess.check~

				#Redirect to configuration.
				if( isDataCorrect ):
					self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
				else:
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)

		if(self.path == '/pmnormal'):
			#Session check
			if (cookie_storage.check_session(self.headers)):
				#TODO eliminar datos de otros modos, overclock etc.
				print "[Power mode normal Post]"
				self.setPowerSavingModeNormal()
				utils.setConfiguration("powermode", "0")
				self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)
			
		if(self.path == '/pm1'):
			#Session check
			if (cookie_storage.check_session(self.headers)):
				#TODO pmnormal.sh -> wifi activado, con underclock, eliminar datos que generen los otros modos etc
				print "[Power mode 1 Post]"
				self.setPowerSavingMode1()
				utils.setConfiguration("powermode", "1")
				self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)

		if(self.path == '/pm2_multiple'):
			if (cookie_storage.check_session(self.headers)):
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
				if(utils.validateInterval_multiple(form)):
					utils.create_crontab(form, True)
					utils.setConfiguration("powermode", "2")
					self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
				else:
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)

		if(self.path == '/pm2_one'):
			if(cookie_storage.check_session(self.headers)):
				configuration_path = './html/configuration_mode2.html'
				print "[Power mode 2 Post: One interval]"

				#Post form recover
				form = cgi.FieldStorage(
					fp=self.rfile,
					headers=self.headers,
					environ={'REQUEST_METHOD':'POST',
							'CONTENT_TYPE':self.headers['Content-Type'],
							})

				#validation
				if(utils.validateInterval(form["start"].value, form["end"].value)):
					monday = tuesday = wednesday = thursday = friday = saturday = sunday = (int(form["start"].value),int(form["end"].value))
					utils.write_crontab([monday, tuesday, wednesday, thursday, friday, saturday, sunday], False)
					utils.setConfiguration("powermode", "2")
					self.answerPost(curdir + sep + "html/configuration-changed.html",200)
				else:
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)

		if(self.path == '/pm2_eachday'):
			if (cookie_storage.check_session(self.headers)):
				configuration_path = './html/configuration_mode2.html'
				print "[Power mode 2 Post: Multiple intervals]"

				#Post form recover
				form = cgi.FieldStorage(
					fp=self.rfile,
					headers=self.headers,
					environ={'REQUEST_METHOD':'POST',
							'CONTENT_TYPE':self.headers['Content-Type'],
							})

				if(utils.validateInterval_eachDay(form)):
					utils.create_crontab(form, False)
					utils.setConfiguration("powermode", "2")
					self.answerPost(curdir + sep + "html/configuration-changed.html", 200)
				else:
					self.answerPost(curdir + sep + "html/configuration-fail.html", 200)
			else:
				self.answerPost(curdir + sep + "html/session-fail.html", 200)

		if(self.path == '/pm3'):
			configuration_path = './html/configuration_mode3.html'
			print "[Power mode 3 Post]"
			utils.setConfiguration("powermode", "3")
			#TODO modo 3 -> pmsleep.sh -> depender del RTC para encender raspi antes de cada medida o en la fecha pedida por el usuario
			#hay que eliminar los datos generados por los otros modos y generar los datos necesarios.
try:
	#Create a web server and define the handler to manage the
	#incoming request
	ip_configuration()
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
