import sys
import urllib2
import urllib
import json
import urlparse
from appDetails import *

class GenToken:
	
	def __init__(self):
		self.app_id = app_id
		self.app_secret = app_secret
		self.redirect_url = redirect_url

	def getAppToken(self):
		url = "https://graph.facebook.com/oauth/access_token?client_id="+self.app_id+"&client_secret="+self.app_secret+"&grant_type=client_credentials"
		try:
			request = urllib2.urlopen(url)
			response = request.read()
			data = response.rsplit("=")
			app_access_token = data[1]
		except Exception, e:
			print e

		return app_access_token

	def verifyAccess(self,access_token):
                app_access_token = self.getAppToken()
		url = "https://graph.facebook.com/debug_token?input_token="+access_token+"&access_token="+app_access_token
		try:
			response = urllib2.urlopen(url)
			data = json.loads(response.read())
		except Exception, e:
			print e

		return data["data"]["is_valid"]

	def parseResponse(self,data):
                nvps={};
                list = data.rsplit("&")
                for el in list:
                        nvplist = el.rsplit("=")
                        nvps[nvplist[0]]=nvplist[1]
                return nvps

	def getAccessToken(self,code):
 		access_token_details = {}
		url =  "https://graph.facebook.com/oauth/access_token?client_id="+self.app_id+"&redirect_uri="+self.redirect_url+"&client_secret="+self.app_secret+"&code="+code;
		req = urllib2.Request(url)
		try: 
			response = urllib2.urlopen(req)
			data = response.read()
			access_token_details = self.parseResponse(data)
                        print "[Access Token]",access_token_details["access_token"]

		except Exception, e:
			print e
		return access_token_details
