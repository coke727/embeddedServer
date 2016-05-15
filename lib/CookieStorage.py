from datetime import datetime, timedelta
import Cookie

""" Implementation of a cookie storage in order to keep a session in the web server.
"""
class CookieStorage(object):

	def __init__(self):
		self.cookies = []

	#Check if cookie is stored in server.
	#TODO comprobar que se eliminan correctamente.
	def check_cookie( self, cookie ):
		""" Check if the cookie is alive and if is sored in the cookie storage. During the search of the cookie in the cookie storage
		the function will remove all the cookies which are not alive.

		:return: True if all is correct or False if not
		:rtype: boolean
		"""
		for c in self.cookies:
			if(c[0]["cookietemp"].value == cookie["cookietemp"].value):
				return True
			else: #Check if cookie is alive
				if( c[1] < datetime.now()):
					self.cookies.remove(c)
		return False

	def store_cookie( self, cookie ):
		""" Stores cookie in the cookie storage.

		:param cookie: cookie to store.
		:type cookie: Cookie
		"""
		self.cookies.append(( cookie, datetime.now() + timedelta(0, int(cookie['cookietemp']['expires']))))

	def check_session( self, headers):
		""" Check in the request headers if exist a valid session or not. 

		:param headers: headers of the request.
		:type headers: string[]
		:return: True if the session exist and False if not.
		:rtype: boolean
		"""
		if "Cookie" in headers:
			c = Cookie.SimpleCookie(headers["Cookie"])
			#Cookie validation
			if(self.check_cookie(c)):
				return True
			else:
				return False
		else:
			return False
