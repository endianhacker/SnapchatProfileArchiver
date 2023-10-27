import requests
from bs4 import BeautifulSoup
import argparse

import json
import datetime
import argparse
import time
import pandas as pd
import math
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dateutil.parser import isoparse
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
from snap import ItemList, ItemListJSONEncoder, userProfile, userProfileJSONEncoder, story, storyJSONEnconder, spotlight, spotlightJSONEncoder
import filetype
def download_snaps(group, output_dir = "./Output"):
       
        for snap in group:
            #input(snap)
            filedata = requests.get(snap.url).content
            kind = filetype.guess(filedata)
            extension = kind.extension
            fpath = os.path.join(output_dir, f"{snap.snapIndex}-{snap.snapID}.{extension}")
            if os.path.isfile(fpath):
                print(f" - {fpath} already exists.")
                #input(isoparse(snap.create_time).astimezone())
                #input(isoparse(snap.create_time))
                os.utime(fpath, (isoparse(snap.upload_time).astimezone().timestamp(), isoparse(snap.upload_time).timestamp()))
                continue

            
            with open(fpath, "wb") as f:
                
                
                f.write(filedata)
            os.utime(fpath, (isoparse(snap.upload_time).astimezone().timestamp(), isoparse(snap.upload_time).timestamp()))
            print(f" - Downloaded {fpath}.")

def get_snapchat_user_data(url,driver):
    driver.get(url)
    time.sleep(2)
    page_source = driver.page_source
    return page_source

def _parse_ItemList_data(ItemList_in):
    outlist = []
    json_format = {"type_str":"","upload_time":"","url":"","viewcount":0,"username":"","duration":"","width":"","height":"","encoding_format":""}
    for entry in ItemList_in.get("itemListElement"):
        temp_json = json_format.copy()
        temp_json["type_str"] = entry.get("@type")
        temp_json["upload_time"] = entry.get("uploadDate")
        temp_json["url"] = entry.get("contentUrl")
        for interaction_stat in entry.get("interactionStatistic"):
            if interaction_stat["interactionType"].get("@type") == "WatchAction":
                temp_json["viewcount"] = interaction_stat.get("userInteractionCount")
        temp_json["username"] = entry["creator"].get("alternateName")
        temp_json["duration"] = entry.get("duration")
        temp_json["width"] = entry.get("width")
        temp_json["height"] = entry.get("height")
        temp_json["encoding_format"] = entry.get("encodingFormat")
        #input(temp_json)
        s = ItemList(**temp_json)
        outlist.append(s)
    #input(outlist)
    return outlist

def _parse_storydata(story_dict):
    
    #$input(story_dict)
    outlist = []
    json_format = {"snapIndex":0,"snapID":"","url":"","upload_time":""}
    for entry in story_dict.get("snapList"):
        #input(entry)
        temp_json = json_format.copy()
        #input(entry)
        temp_json["snapIndex"] = entry.get("snapIndex")
        temp_json["snapID"] = entry["snapId"].get("value")
        temp_json["url"] = entry["snapUrls"].get("mediaUrl")
        temp_json["upload_time"] = datetime.datetime.utcfromtimestamp(int(entry["timestampInSec"].get("value"))).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        #input(temp_json)
        s = story(**temp_json.copy())
        outlist.append(s)
    
    return outlist

def _parse_spotlightdata(nextdata_in):
    spotlight_list = nextdata_in["props"]["pageProps"].get("spotlightHighlights")
    json_format = {"storyId":"", "storyTitle":"", "snapList":[], "snapList_len":0}
    outlist = []
    if spotlight_list == None:
        return None

    for spotlight_entry in spotlight_list:
        temp_json = json_format.copy()
        temp_json["storyId"] = spotlight_entry["storyId"].get("value")
        temp_json["storyTitle"] = spotlight_entry["storyTitle"].get("value")
        temp_json["snapList"] = _parse_storydata(spotlight_entry)
        temp_json["snapList_len"] = len(temp_json["snapList"])
       # input(temp_json)
        s = spotlight(**temp_json)
        outlist.append(s)
    return outlist
        
def _parse_userprofile_data(nextdata_in):
    userprofile_dict = nextdata_in["props"]["pageProps"].get("userProfile")
    temp_json = {"username": "", "title":"", "snapcodeImageUrl":""}
    if userprofile_dict.get("$case") == "userInfo":
        temp_json["username"] = userprofile_dict[userprofile_dict.get("$case")].get("username")
        temp_json["title"] = userprofile_dict[userprofile_dict.get("$case")].get("displayName")
        temp_json["snapcodeImageUrl"] = userprofile_dict[userprofile_dict.get("$case")].get("snapcodeImageUrl")
    if userprofile_dict.get("$case") == "publicProfileInfo":
        temp_json["username"] = userprofile_dict[userprofile_dict.get("$case")].get("username")
        temp_json["title"] = userprofile_dict[userprofile_dict.get("$case")].get("title")
        temp_json["snapcodeImageUrl"] = userprofile_dict[userprofile_dict.get("$case")].get("snapcodeImageUrl")
        temp_json["badge"] = userprofile_dict[userprofile_dict.get("$case")].get("badge")
        temp_json["categoryStringId"] = userprofile_dict[userprofile_dict.get("$case")].get("categoryStringId")
        temp_json["subscriberCount"] = int(userprofile_dict[userprofile_dict.get("$case")].get("subscriberCount"))
        temp_json["bio"] = userprofile_dict[userprofile_dict.get("$case")].get("bio")
        temp_json["websiteurl"] = userprofile_dict[userprofile_dict.get("$case")].get("websiteUrl")
        temp_json["profile_url"] = userprofile_dict[userprofile_dict.get("$case")].get("profilePictureUrl")
        temp_json["address"] = userprofile_dict[userprofile_dict.get("$case")].get("address")

    s = userProfile(**temp_json)
    return s
def parse_user_data(user_data):
    soup = BeautifulSoup(user_data, "html.parser")
    itemList_results = soup.find(id="ItemList")
    nextdata_results = soup.find(id="__NEXT_DATA__")
    
    if nextdata_results != None:
        nextdata_json = json.loads(nextdata_results.text)
        story_dict = nextdata_json["props"]["pageProps"].get("story")
        #input(story_dict)
        if story_dict != None:
            parsed_storydict = _parse_storydata(story_dict)
        else:
            parsed_storydict = None
        parsed_spotlightdict = _parse_spotlightdata(nextdata_json)
        parsed_userprofile = _parse_userprofile_data(nextdata_json)
    try:
        if itemList_results != None:
            itemList_json = json.loads(itemList_results.text)
            outfile = open("output.json","w+")
            outfile.write(json.dumps(itemList_json))
            outfile.close()
            parsed_itemlist = _parse_ItemList_data(itemList_json)
    except Exception as e:
        print(e)
   
    
    return parsed_userprofile, parsed_spotlightdict, parsed_storydict



chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
total_server_errors = 0
total_timeouts = 0


parser = argparse.ArgumentParser(prog='SnapchatArchiver', description='OSINT archive snapchat user\r\n')
parser.add_argument("-u",'--user',help="target username", required=True)
parser.add_argument("--write_json", help="json output", required=False, default = 0)

args = parser.parse_args()

args.user = args.user.replace("@","")
#create snapchat username url
url = f"https://snapchat.com/add/{args.user}"
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

user_data = get_snapchat_user_data(url, driver)
snapshot = open(f"{args.user}_snapshot_{int(datetime.datetime.now().timestamp())}.html","w+b")
snapshot.write(user_data.encode())
snapshot.close()
driver.close()
user_info, spotlight_parsed, story_parsed =  parse_user_data(user_data)
#input(spotlight_parsed)
#input(story_parsed)

time_dir = datetime.datetime.utcfromtimestamp(int(datetime.datetime.now().timestamp())).strftime('%Y-%m-%d')

if args.write_json:
    user_info_out = open(f"{args.user}_userinfo.json", "w+")
    user_info_out.write(json.dumps(user_info, cls=userProfileJSONEncoder))
    user_info_out.close()

if args.write_json:

    spotlight_parsed_out = open(f"{args.user}_spotlight_{int(datetime.datetime.now().timestamp())}.json","w+")
spotlight_dir = f"./{args.user}_Spotlight/"
try:
    os.mkdir(spotlight_dir)
except Exception as e:
    print(e)
spotlight_dir += time_dir
try:
    os.mkdir(spotlight_dir)
except Exception as e:
    print(e)

if spotlight_parsed != None:
    for entry in spotlight_parsed:
        
        if args.write_json:
            spotlight_parsed_out.write(json.dumps(entry, cls=spotlightJSONEncoder) + "\n")
            spotlight_parsed_out.flush()
        download_snaps(entry.snapList, spotlight_dir)
    if args.write_json:
        spotlight_parsed_out.close()

if args.write_json:

    story_parsed_out = open(f"{args.user}_story_{int(datetime.datetime.now().timestamp())}.json","w+")
story_dir = f"./{args.user}_Story/"
try:
    os.mkdir(story_dir)
except Exception as e:
    print(e)
story_dir += time_dir
try:
    os.mkdir(story_dir)
except Exception as e:
    print(e)
if story_parsed != None:
    for entry in story_parsed:
        if args.write_json:
            story_parsed_out.write(json.dumps(entry, cls=storyJSONEnconder) + "\n")
            story_parsed_out.flush()
    if args.write_json:
        story_parsed_out.close()
    download_snaps(story_parsed, output_dir=story_dir)


#itemList_df = pd.read_json(pd.read_html(user_data, attrs= {"id":"ItemList"})[0])
#input(itemList_df)


#s = Snap(**data_dict) translation
