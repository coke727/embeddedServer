#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep
import SimpleHTTPServer
import SocketServer
import logging
import cgi
import sys

PORT_NUMBER = 8080
samples_show = 20
scp_adress = ""
frequency = 0

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):


	def getSamples(n):
		with open("samples.txt") as myfile:
			head = [next(myfile) for x in xrange(n)]
		print head

	@staticmethod
	def create_web(num_samples):
		with open("html/web.html",'w+') as new_file:
			with open("html/web_bone.html") as old_file:
				for line in old_file:
					new_file.write(line)
			with open("samples.txt") as samples:
				for i, line in enumerate(samples):
					tupla = [x.strip() for x in line.split(';')]
					new_file.write("<tr><td>" + tupla[0] + "</td><td>" + tupla[1] + "</td></tr>")
					if i == num_samples - 1:
						break
			new_file.write("</table></article><aside><div id='chart_div'></div></aside></body></html>")
		old_file.close()
	
	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			self.create_web(samples_show)
			self.path="html/web.html"
		if self.path=="/configuration":
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
				#create_web(10)
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
			# TODO para almacenar en un log: print (self.headers)
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})
			
			login = form["login"].value
			password = form["password"].value
			#TODO Check login and pass

			f = open(curdir + sep + "html/configuration.html") 
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()

		if(self.path == '/configuration'):
			global samples_show
			global scp_adress
			global frequency

			print "[Configuration Post]"
			# TODO store in log: print (self.headers)
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						'CONTENT_TYPE':self.headers['Content-Type'],
						})

			samples_show = int(form["samples"].value)
			scp_adress = form["scp"].value
			frequency = int(form["frequency"].value)

			f = open(curdir + sep + "html/configuration.html") 
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write(f.read())
			f.close()

try:
	#Create a web server and define the handler to manage the
	#incoming request
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER
	
	#Wait forever for incoming htto requests
	server.serve_forever()

except KeyboardInterrupt:
	
	print '^C received, shutting down the web server'
	server.socket.close()