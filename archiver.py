import requests
from bs4 import BeautifulSoup
import argparse
import sys
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
import subprocess



def download_snaps(group, output_dir = "./Output"):
       
        for snap in group:
            #input(snap)
            filedata = requests.get(snap.url).content
            kind = filetype.guess(filedata)
            try:
                extension = kind.extension
            except Exception as e:
                extension = "file"
            if "Story/" in output_dir:
                fpath = os.path.join(output_dir, f"{snap.snapID}.{extension}")
            else:
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
    if userprofile_dict == None:
        print("[+] Profile is private or deleted!")
        return None
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
        temp_json["relatedAccountsInfo"] = userprofile_dict[userprofile_dict.get("$case")].get("relatedAccountsInfo")


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

def download_profile(username, arg_output_dir = "./", write_json_flag = 0, related_archive_flag = 0, deep_archive_flag = 0, username_list = [], recursive_flag = 0):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    total_server_errors = 0
    total_timeouts = 0
    username_list_temp = []
    

    url = f"https://snapchat.com/add/{username}"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    if recursive_flag == 1:
        
        output_dir = arg_output_dir + "/" + username
    else:
        output_dir = arg_output_dir + "/" + username
    print(username_list)
    if username in username_list:
        print(f"Recursive Error on {username}")
        return None
    
    try:
        os.mkdir(output_dir)
    except Exception as e:
        print(e)

    user_data = get_snapchat_user_data(url, driver)
    snapshot = open(f"{output_dir}/snapshot_{int(datetime.datetime.now().timestamp())}.html","w+b")
    snapshot.write(user_data.encode())
    snapshot.close()
    driver.close()
    user_info, spotlight_parsed, story_parsed =  parse_user_data(user_data)
    #input(spotlight_parsed)

    if user_info == None:
        return None
    #input(story_parsed)

    time_dir = datetime.datetime.utcfromtimestamp(int(datetime.datetime.now().timestamp())).strftime('%Y-%m-%d')


    if args.write_json:
        user_info_out = open(f"{output_dir}/userinfo.json", "w+")
        user_info_out.write(json.dumps(user_info, cls=userProfileJSONEncoder))
        user_info_out.close()

    if args.write_json:

        spotlight_parsed_out = open(f"{output_dir}/spotlight_{int(datetime.datetime.now().timestamp())}.json","w+")
    spotlight_dir = f"{output_dir}/Spotlight/"
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

    if write_json_flag:

        story_parsed_out = open(f"{output_dir}/story_{int(datetime.datetime.now().timestamp())}.json","w+")
    story_dir = f"{output_dir}/Story/"
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
    if related_archive_flag != 0:
        if recursive_flag == 0:
            related_accounts_dir = f"{output_dir}/Related_Accounts/"
        else:
            related_accounts_dir = f"{arg_output_dir}/"
        
       # input(related_accounts_dir)
        try:
            os.mkdir(related_accounts_dir)
        except Exception as e:
            print(e)

        username_list.append(username)
        for entry in user_info.relatedAccountsInfo:
            
        
            username_in = entry["publicProfileInfo"].get("username")
           # username_list.append(username)
           # username_list = list(set(username_list))
            #input(username)

            temp_out_dir  = os.path.abspath(related_accounts_dir)
            if args.deep_archive != 0:
               username_list_temp =  download_profile(username_in, related_accounts_dir, write_json_flag = 1, related_archive_flag = 1, deep_archive_flag = 1, username_list=username_list, recursive_flag = 1)
            else:
                username_list_temp = download_profile(username_in, related_accounts_dir, write_json_flag = args.write_json, related_archive_flag = 1, deep_archive_flag = 0, username_list = username_list)


        
        if username_list_temp != None:
           # input(username_list_temp)
            for i  in range(len(username_list_temp)):
              #  input("hit")
                username_list.append(username_list_temp[i])
               # input(username_list)
        username_list = list(set(username_list)) 

        #print(username_list)

        return username_list
    
    if related_archive_flag == 0:
        username_list.append(username)
       # input(username_list)
        return username_list
        


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
total_server_errors = 0
total_timeouts = 0


parser = argparse.ArgumentParser(prog='SnapchatArchiver', description='OSINT archive snapchat user\r\n')
parser.add_argument("-u",'--user',help="target username", required=True)
parser.add_argument("--write_json", help="json output", required=False, default = 0)
parser.add_argument("--output_dir", help="change the output directory", required = False, default = "./")
parser.add_argument("--related_archive", help="archive related accounts, too.", required = False, default = 0)
parser.add_argument("--deep_archive", help="recursive archiving related accounts, WARNING EXPERIMENTAL, MAY RUN FOR AN EXTREMELY LONG TIME", required = False, default = 0)
args = parser.parse_args()

args.user = args.user.replace("@","")
#create snapchat username url
url = f"https://snapchat.com/add/{args.user}"
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
output_dir = args.output_dir + "/" + args.user
if args.user in args.output_dir:
    print(f"Recursive Alert! on {args.user} and {args.output_dir}")
    sys.exit()
try:
    os.mkdir(output_dir)
except Exception as e:
    print(e)

user_data = get_snapchat_user_data(url, driver)
snapshot = open(f"{output_dir}/snapshot_{int(datetime.datetime.now().timestamp())}.html","w+b")
snapshot.write(user_data.encode())
snapshot.close()
driver.close()
user_info, spotlight_parsed, story_parsed =  parse_user_data(user_data)
#input(spotlight_parsed)

if user_info == None:
    sys.exit()
#input(story_parsed)

time_dir = datetime.datetime.utcfromtimestamp(int(datetime.datetime.now().timestamp())).strftime('%Y-%m-%d')


if args.write_json:
    user_info_out = open(f"{output_dir}/userinfo.json", "w+")
    user_info_out.write(json.dumps(user_info, cls=userProfileJSONEncoder))
    user_info_out.close()

if args.write_json:

    spotlight_parsed_out = open(f"{output_dir}/spotlight_{int(datetime.datetime.now().timestamp())}.json","w+")
spotlight_dir = f"{output_dir}/Spotlight/"
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

    story_parsed_out = open(f"{output_dir}/story_{int(datetime.datetime.now().timestamp())}.json","w+")
story_dir = f"{output_dir}/Story/"
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

if args.related_archive != 0:
    related_accounts_dir = f"{output_dir}/Related_Accounts/"
    try:
        os.mkdir(related_accounts_dir)
    except Exception as e:
        print(e)
    #input(user_info)
    username_list = []
    for entry in user_info.relatedAccountsInfo:
        
        username = entry["publicProfileInfo"].get("username")
        
        
        #input(username)

        temp_out_dir  = os.path.abspath(related_accounts_dir)

        if args.deep_archive != 0:
            username_list_temp = download_profile(username, related_accounts_dir, write_json_flag = args.write_json, related_archive_flag = 1, deep_archive_flag = 1, username_list=username_list, recursive_flag = 1)

            #process = subprocess.Popen(f"py ./archiver.py -u {username} --write_json 1 --output_dir {temp_out_dir} --related_archive 1 --deep_archive 1", shell=True)
        else:

            #process = subprocess.Popen(f"py ./archiver.py -u {username} --write_json 1 --output_dir {temp_out_dir}", shell=True)
           username_list_temp = download_profile(username, related_accounts_dir, write_json_flag = args.write_json, related_archive_flag = 0, deep_archive_flag = 0, username_list = username_list)

        username_list.append(username)
        if username_list_temp != None:
           # input(username_list_temp)
            for i  in range(len(username_list_temp)):
              #  input("hit")
                username_list.append(username_list_temp[i])
               # input(username_list)
        username_list = list(set(username_list))        

        #return username_list

    
        #stdout, stderr = process.communicate()
        

    output_accounts_file = open(related_accounts_dir + str(int(datetime.datetime.now().timestamp())) + "_username_list.txt", "w+")
    for entry in username_list:
        output_accounts_file.write(entry + "\n")
        output_accounts_file.flush()
    output_accounts_file.close()

#itemList_df = pd.read_json(pd.read_html(user_data, attrs= {"id":"ItemList"})[0])
#input(itemList_df)


#s = Snap(**data_dict) translation
