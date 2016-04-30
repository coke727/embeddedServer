from os import listdir, stat
from os.path import isfile, join

samples_path ="./data/"

def create_empty(self):
	with open("html/web.html",'w+') as new_file:
		with open("html/empty_web.html") as old_file:
			for line in old_file:
				new_file.write(line)

def create_web(num_samples):
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
