import facebook
import pprint
import json
import urllib2
import pymongo
from pymongo import *
from getToken import *
from appDetails import *
import re
import urllib

class FbData:
	def __init__(self):

                self.report = Connection()["fbData"]["fb_reports"]
                self.t = GenToken()

        def getAccessCode(self,code):

                token_details = self.t.getAccessToken(code)
                self.oauth_access_token = token_details["access_token"]
                token_details["platform_type"] = "facebook"
                self.report.insert(token_details)
        
        def getStoredAccessToken(self):
                stored_token = self.report.find_one({"platform_type":"facebook"})
                if stored_token is None:
                        print "Generate a new code!!"
                        exit(0)
                valid = self.t.verifyAccess(stored_token["access_token"])
                
                if valid is "false":
                        self.report.remove({"access_token":stored_token["access_token"]})
                        print "Generate a new code!!"
                        exit(0)
                else:
                        self.oauth_access_token = stored_token["access_token"]

        def graphConnection(self):
        
		self.graph = facebook.GraphAPI(self.oauth_access_token)
                #page_id present in appDetails.py
                #query = "/"+str(page_id)+"/posts"
                url = "https://graph.facebook.com/"+str(page_id)+"/posts?access_token="+str(self.oauth_access_token)+"&since="+str(since)+"&until="+str(until)
		#data = self.graph.get_object(query)
                response = urllib2.urlopen(url)
                response = response.read()
                data = json.loads(response)
		all_posts = []
                #no_of_likes,no_of_comments,no_of_posts present in appDetails.py
		self.no_of_likes = no_of_likes
		self.no_of_comments = no_of_comments
		self.no_of_posts = no_of_posts
		self.getData(all_posts,data)

        def getPage(self,url):

		response = urllib2.urlopen(url)
		new_data = response.read()
		new_data = json.loads(new_data)
		return new_data

        def getShares(self,id):
                url = "https://graph.facebook.com/"+str(id)+"?fields=shares&access_token="+str(self.oauth_access_token)
                response = urllib2.urlopen(url)
                share_obj = response.read()
                share_obj = json.loads(share_obj)
                if "shares" in share_obj:
                        count = share_obj["shares"]["count"]
                else:
                        count = 0
                return count

        def getUserId(self,like_id):
                #url = "https://graph.facebook.com/"+str(like_id)+"?access_token="+str(self.oauth_access_token)
                #response = urllib2.urlopen(url)
                #like_id_obj = response.read()
                #like_id_obj = json.loads(like_id_obj)
                like_id_obj = self.graph.get_object(like_id)
                match = re.search(r'profile.php',like_id_obj["link"])
                if match:
                        data = like_id_obj["link"].rsplit("profile.php?id=")
                        user_id = data[1]
                else:
                        uid = re.sub("https://www.facebook.com/","",like_id_obj["link"])
                        graph_url = "https://graph.facebook.com/"
                        link = urllib.urlopen(graph_url + uid)
                        response = link.read()
                        data = json.loads(response)
                        user_id = data["id"]
                #asu_id = profile_url.rsplit("app_scoped_user_id%2F")
                #user_id = asu_id[1]
                return user_id

	def getComments(self,comments_data,comments_list):

		for comment in comments_data["data"]:
			comments_list[0]["count"] += 1
			if comments_list[0]["count"] <= self.no_of_comments:	
				comment_obj = {}
				comment_obj["id"] = comment["from"]["id"]
				comment_obj["message"] = comment["message"]
				comment_obj["created_time"] = comment["created_time"]
				comment_obj["user_likes"] = comment["user_likes"]
				comments_list.append(comment_obj)
			else:
				pass

		if "paging" in comments_data:
			if "next" in comments_data["paging"]:
				url = comments_data["paging"]["next"]
				next_comments_data = self.getPage(url)
				self.getComments(next_comments_data,comments_list)

		return comments_list

	def getLikes(self,likes_data,likes_list):
		
		for like in likes_data["data"]:
			likes_list[0]["count"] += 1
			if likes_list[0]["count"] <= self.no_of_likes:
				likes_obj = {}
				likes_obj["like_id"] = like["id"]
                                likes_obj["user_id"] = self.getUserId(like["id"])
				likes_obj["name"] = like["name"]
				likes_list.append(likes_obj)
			else:
				pass

		if "paging" in likes_data:
			if "next" in likes_data["paging"]:
				url = likes_data["paging"]["next"]
				next_likes_data = self.getPage(url)
				self.getLikes(next_likes_data,likes_list)

		return likes_list
				

	def extractData(self,data,all_posts):
		
		for post in data["data"]:
			if len(all_posts) < self.no_of_posts:
				data_obj = {}
				if "id" in post:
					data_obj["id"] = post["id"]
                                        data_obj["shares"] = self.getShares(post["id"])

				if "message" in post:
					data_obj["message"] = post["message"]

				if "picture" in post:
					data_obj["picture"] = post["picture"]

				if "type" in post:
					data_obj["type"] = post["type"]
					if post["type"] == "video":
						data_obj["source"] = post["source"]
					if post["type"] == "link":
						data_obj["link"] = post["link"]

				if "created_time" in post:
					data_obj["created_time"] = post["created_time"]

				if "likes" in post:
					likes_list = [{"count":0}]
					likes_list = self.getLikes(post["likes"],likes_list)
					data_obj["likes"] = likes_list
			
				if "comments" in post:
					comments_list = [{"count":0}]
					comments_list = self.getComments(post["comments"],comments_list)
					data_obj["comments"] = comments_list
				
                                data_obj["platform"] = "facebook"
                                print data_obj
				self.report.insert(data_obj)
				all_posts.append(data_obj)
			else:
				break
		return all_posts
		
	def getData(self,all_posts,data):
	    all_posts = self.extractData(data,all_posts)
	    self.getAllPreviousPosts(all_posts,data)
	    print "number of previous post are ", len(all_posts)
	    self.getAllNextPosts(all_posts,data)
	    print "[INFO]The total number of posts are:",len(all_posts)

	def getAllNextPosts(self,all_posts,data):
		if len(all_posts) >= self.no_of_posts:
			return "done!!"
		if "paging" in data:
		    if "next" in data["paging"]:
			    url = data["paging"]["next"]
			    new_data = self.getPage(url)
			    
			    all_posts = self.extractData(new_data,all_posts)
			    print "[Count] is ", len(all_posts)
			    self.getAllNextPosts(all_posts,new_data)
		return "done!!"

	def getAllPreviousPosts(self,all_posts,data):
		if len(all_posts) >= self.no_of_posts:
				return "done!!"
		if "paging" in data:
			print "in previous function"
			if "previous" in data["paging"]:
			    url = data["paging"]["previous"]
			    new_data = self.getPage(url)
				
			    all_posts = self.extractData(new_data,all_posts)
			    print "[Count] is", len(all_posts)
			    self.getAllPreviousPosts(all_posts,new_data)
		return "done!!"
