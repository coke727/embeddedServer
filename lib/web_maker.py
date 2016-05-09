from os import listdir, stat, system
from os.path import isfile, join
import utils

samples_path ="./data/"

""" HTML web page builder.

Build and changes the parameters of the web pages which the web server shows using diferent templates stored in the server.

"""
def create_empty(self):
	""" Changes the home web page code for show a home page without any samples and graphics.
	For create the empty web page this function use the emplty_web.html template stored in the templates folder.
	"""
	with open("html/web.html",'w+') as new_file:
		with open("html/empty_web.html") as old_file:
			for line in old_file:
				new_file.write(line)

def create_web(num_samples):
	""" Create a home web page with a determinate numbre of samples.

	:param num_samples: number of samples added to the html file.
	:type num_samples: int

	This function will use the web_bone.html template stored in the templates directory.

	The samples will be get from the data files in the data folder getting always the last taken samples.
	"""
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

def make_pages(domain):
	""" Change the domain in the links of the web pages.

	:param domain: new domain.
	:type domain: string
	"""
	templates = [f for f in listdir("html/templates/") if isfile(join("html/templates/", f))]
	for template in templates:
		set_domain(template, domain)

def set_domain(path, domain):
	""" Change the domain in one of the htmls.

	:param domain: new domain.
	:type domain: string
	:param path: name of the file the function will change.
	:type path: string
	"""
	with file("html/templates/"+path,'r') as template:
		with open("html/"+path, 'w+') as page:
			for line in template:
				page.write(line.replace('localhost', domain))
	template.close()

def changeDeviceDomain(newip):
	""" Change the device name in the /etc/hostname and in /etc/hosts.
	The device domain is generated with the actual ip in order to get a domain in the FIT faculty of VUT university.
	
	:param newip: The new ip the function will use for generate the new domain.
	:type domain: string.
	"""
	domain = ".fit.vutbr.cz"
	hostname = "dhcpr"
	machine_number = "000"

	ip = newip.split('.')

	if (int(ip[3]) == 179):
		hostname = "dhcps"
	elif (int(ip[3]) == 178):
		hostname = "dhcpr"
	if ( int(ip[3]) < 10 ):
		machine_number = "00"+ip[3]
	elif (int(ip[3]) < 100):
		machine_number = "0"+ip[3]
	elif (int(ip[3]) < 1000):
		machine_number = ip[3]

	make_pages(hostname+machine_number+domain)
	system('sudo echo "' +hostname+machine_number+ '" > /etc/hostname')
	system('sudo echo -e "' +newip+ '\t' +hostname+machine_number+domain +'\t'+ hostname+machine_number+'\n" >> /etc/hosts')
	system('sudo /etc/init.d/hostname.sh')
	system('sudo reboot')

	utils.setConfiguration("domain", hostname+machine_number+domain)
    