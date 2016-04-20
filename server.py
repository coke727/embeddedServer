#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import ssl
from os import curdir, sep
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys
import re
import base64
import subprocess
from subprocess import PIPE
import Cookie
from datetime import datetime, timedelta

PORT_NUMBER = 80
samples_show = 20
scp_adress = ""
scp_frequency = 0
frequency = 0
cookies = []

#This class will handles any incoming request from the browser 
class myHandler(BaseHTTPRequestHandler):

	@staticmethod
	def isInt(s):
		try: 
			int(s)
			return True
		except ValueError:
			return False

	def getSamples(n):
		with open("data/samples.txt") as myfile:
			head = [next(myfile) for x in xrange(n)]
		print head

	@staticmethod
	def create_web(num_samples):
		with open("html/web.html",'w+') as new_file:
			with open("html/web_bone.html") as old_file:
				for line in old_file:
					new_file.write(line)
			with open("data/samples.txt") as samples:
				for i, line in enumerate(samples):
					tupla = [x.strip() for x in line.split(';')]
					new_file.write("<tr><td>" + tupla[0] + "</td><td>" + tupla[1] + "</td></tr>")
					if i == num_samples - 1:
						break
			new_file.write("</table></article></body></html>")
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

	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			self.create_web(samples_show)
			self.path="html/web.html"
		if self.path=="/configuration":
			if "Cookie" in self.headers:
				c = Cookie.SimpleCookie(self.headers["Cookie"])
				if(self.check_cookie(c)):
					self.path="html/configuration.html"
				else:
					self.path="html/login.html"
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
		if(self.path == '/login'):
			print "[Login Post]"
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})
			
			login = form["login"].value
			password = form["password"].value
			if(True): #TODO Check login and pass
				#Cookie creation
				c = Cookie.SimpleCookie()
				c['cookietemp'] = "cookie-oreo" #TODO setear valor de cookie, debe ser diferente para cada cookie
				c['cookietemp']['domain'] = "localhost:8080"
				c['cookietemp']['expires'] = 12000
				c['cookietemp']['path'] = "/configuration"
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
						#TODO Change frequency function when sensor is installed
						if( self.isInt( form["samples"].value ) and int( form["samples"].value ) > 0 ):
							samples_show = int(form["samples"].value)
						else:
							isDataCorrect = False

						if( self.isInt( form["frequency"].value ) and int( form["frequency"].value ) > 0 ):
							frequency = int(form["frequency"].value)
							os.system("python tempdaemon.py restart " + str(frequency))
						else:
							isDataCorrect = False

						if( isDataCorrect ):
							f = open(curdir + sep + "html/configuration-conf.html")
							self.send_response(200)
						else:
							f = open(curdir + sep + "html/configuration-conf-fail.html")
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
			isDataCorrect = False

			print "[SCP Post]"
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			#Data validation
			if self.isInt(form["scpfrequency"].value) and self.isInt(form["port"].value) and form["scp"].value and form["user"].value and form["directory"].value and form["password"].value:
				isDataCorrect = True

			#Create scp task.
			#TODO encriptar datos que se pasan al script (?)
			p = subprocess.Popen(["python", "scpdaemon.py", "restart", form["scpfrequency"].value, form["scp"].value, form["user"].value, form["port"].value, form["directory"].value], stdin=PIPE, stdout=PIPE)
			print p.communicate(form["password"].value)
			#TODO check that is correct, subprocess.check~

			#Redirect to configuration.
			if( isDataCorrect ):
				f = open(curdir + sep + "html/configuration-scp.html") 
				self.send_response(200)
			else:
				f = open(curdir + sep + "html/configuration-scp-fail.html") 
				self.send_response(402)

			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()

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
