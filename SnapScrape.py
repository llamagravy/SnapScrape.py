#!/usr/bin/python3
__author__ = "https://codeberg.org/allendema" #modified by llamagravy

from time import sleep
import datetime
import subprocess
import time
import json
import sys
import os
from requests.exceptions import ChunkedEncodingError
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

def user_input():
    """Check for username argument
    Otherwise get it from user input"""

    try:
        username = sys.argv[1]
    except Exception:
        username = input("Enter a username: ")

    path = username

    if os.path.exists(path):
        print("This user has a folder in your System.")

    else:
        os.mkdir(path)

    os.chdir(path)

    return username


YELLOW = "\033[1;32;40m"
RED = "\033[31m"

headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/103.0.2'}

base_url = "https://story.snapchat.com/@"
username = user_input()

mix = base_url + username
print(mix)


def get_json():
    """Get JSON from Snapchat"""
    
    r = requests.get(mix, headers=headers)
    if r.ok:
        pass
    else:
        sys.exit(f"{RED}Unable to connect to Snapchat. Make sure the username is correct.")

    soup = BeautifulSoup(r.content, "html.parser")
    
    # Find script with JSON data on site
    snaps = soup.find(id="__NEXT_DATA__").string.strip()

    data = json.loads(snaps)

    timestamp = time.strftime("%Y%m%d-%H%M%S")

    with open(f"profile_metadata_{timestamp}.json", "w") as f:
        json.dump(data, f, indent=4)


    return data


def profile_metadata(json_dict=get_json()):
    """Detect public profile, then print bio, bitmoji, and download media files."""

    try:
        # Extract URLs and bio
        bitmoji = json_dict["props"]["pageProps"]["userProfile"]["publicProfileInfo"]["snapcodeImageUrl"]
        bio = json_dict["props"]["pageProps"]["userProfile"]["publicProfileInfo"]["bio"]
        pfp = json_dict['props']['pageProps']['userProfile']['publicProfileInfo']['profilePictureUrl']
        hero = json_dict['props']['pageProps']['userProfile']['publicProfileInfo']['squareHeroImageUrl']
        ximage = json_dict['props']['pageProps']['linkPreview']['twitterImage']['url']
        fbimage = json_dict['props']['pageProps']['linkPreview']['facebookImage']['url']

        # Download the images and media files using an index counter
        timestamp = time.time()
        
        download_file(bitmoji, 1, 0)
        download_file(pfp, 2, 0)
        if hero == "":
            print(f"{RED}No hero image found")
        else:
            download_file(hero, 3, 0)
        download_file(ximage, 4, 0)
        if ximage != fbimage:
            download_file(fbimage, 5, 0)

        # Save bio to a text file

        with open(f"bio_{timestamp}.txt", "w") as bio_file:
            bio_file.write(f"{bio}\n")
        
        print(f"{YELLOW}Bio saved to bio.txt: {bio}")

    # if not public
    except KeyError:
        bitmoji = json_dict["props"]["pageProps"]["userProfile"]["userInfo"]["snapcodeImageUrl"]
        bio = json_dict["props"]["pageProps"]["userProfile"]["userInfo"]["displayName"]

        print(f"{YELLOW}Here is the Bio: \n {bio}\n")
        print(f"Bitmoji:\n {bitmoji}\n")
        print(f"{RED} This user is private.")

        sys.exit(1)

    print(f"{YELLOW}\nBio of the user:\n", bio)
    print(f"\nHere is the Bitmoji:\n {bitmoji} \n")

    print(f"Getting posts of: {username}\n")


def download_media(json_dict=get_json()):
    """Download stories and curated highlights."""
    indx = 10
    # Stories
    try:
        cwd = os.getcwd()
        if os.path.basename(cwd) in ("stories", "highlights", "spotlight", "lenses"):
            os.chdir("..")

        path = "stories"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        for i in json_dict["props"]["pageProps"]["story"]["snapList"]:
            file_url = i["snapUrls"]["mediaUrl"]
            pre_url = i["snapUrls"]["mediaPreviewUrl"]["value"]
            timestamp = i["timestampInSec"]["value"]

            if file_url == "":
                print(f"{RED}There is a Story but no URL is provided by Snapchat.")
                continue

            if pre_url == "":
                print(f"{RED}There is a Story thumbnail but no URL is provided by Snapchat.")
                continue

            indx += 1
            download_file(file_url, indx, timestamp)
            indx += 1
            download_file(pre_url, indx, timestamp)

    except KeyError as e:
        print(f"{RED}No temporary user stories found for the last 24h.")
    else:
        print(f"\n{YELLOW}Stories found. Successfully Downloaded.")

    # Spotlight Highlights
    try:
        if json_dict["props"]["pageProps"]["spotlightHighlights"] == "":
            print(f"{RED}There are no spotlight highlights found.")
        cwd = os.getcwd()
        if os.path.basename(cwd) in ("stories", "highlights", "spotlight", "lenses"):
            os.chdir("..")

        path = "spotlight"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        for i in json_dict["props"]["pageProps"]["spotlightHighlights"]:
            snap_list = i["snapList"]
            for d in snap_list:
                # Process each item in snapList
                file_url = d["snapUrls"]["mediaUrl"]
                pre_url = d["snapUrls"]["mediaPreviewUrl"]["value"]
                timestamp = d["timestampInSec"]["value"]
                if file_url == "":
                    print(f"{RED}There is a Spotlight Highlight but no URL is provided by Snapchat.")
                    continue
                if pre_url == "":
                    print(f"{RED}There is a Spotlight Highlight thumbnail but no URL is provided by Snapchat.")
                    continue

                indx += 1
                download_file(file_url, indx, timestamp)
                indx += 1
                download_file(pre_url, indx, timestamp)

    except KeyError as e:
        print(f"{RED}No spotlight highlights found. {e}")

    # Curated Highlights
    try:
        if json_dict["props"]["pageProps"]["curatedHighlights"] == "":
            print(f"{RED}There are no curated highlights found.")
        cwd = os.getcwd()
        if os.path.basename(cwd) in ("stories", "highlights", "spotlight", "lenses"):
            os.chdir("..")

        path = "highlights"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        for i in json_dict["props"]["pageProps"]["curatedHighlights"]:
            snap_list = i["snapList"]
            storytitle = i["storyTitle"]["value"]
            cwd = os.getcwd()
            if not os.path.basename(cwd) in ("stories", "highlights", "spotlight", "lenses"):
                os.chdir("..")
            if not os.path.exists(storytitle):
                os.mkdir(storytitle)
            os.chdir(storytitle)
            for d in snap_list:
                # Process each item in snapList
                file_url = d["snapUrls"]["mediaUrl"]
                pre_url = d["snapUrls"]["mediaPreviewUrl"]["value"]
                timestamp = d["timestampInSec"]["value"]
                if file_url == "":
                    print(f"{RED}There is a Curated Highlight but no URL is provided by Snapchat.")
                    continue

                if pre_url == "":
                    print(f"{RED}There is a Curated Highlight thumbnail but no URL is provided by Snapchat.")
                    continue

                indx += 1
                download_file(file_url, indx, timestamp)
                indx += 1
                download_file(pre_url, indx, timestamp)

    except KeyError as e:
        print(f"{RED}No curated highlights found. {e}")

    # Lenses
    try:
        if json_dict["props"]["pageProps"]["lenses"] == "":
            print(f"{RED}There are no lenses found.")
        cwd = os.getcwd()
        if os.path.basename(cwd) in ("stories", "highlights", "spotlight", "lenses"):
            os.chdir("..")

        path = "lenses"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        for i in json_dict["props"]["pageProps"]["lenses"]:
            lpiu = i["lensPreviewImageUrl"]
            lpvu = i["lensPreviewVideoUrl"]
            iu = i["iconUrl"]
            if lpiu == "":
                print(f"{RED}There is a lense but no URL is provided by Snapchat.")
                continue
            if lpvu == "":
                print(f"{RED}There is a lense but no URL is provided by Snapchat.")
                continue
            if iu == "":
                print(f"{RED}There is a lense but no URL is provided by Snapchat.")
                continue

            indx += 1
            download_file(lpiu, indx)
            indx += 1
            download_file(lpvu, indx)
            indx += 1
            download_file(iu, indx)

    except KeyError as e:
        print(f"{RED}No lenses found. {e}")

def download_file(file_url, index, timest):
    """Function to download files."""

    # Send the requests to the URL
    r = requests.get(file_url, stream=True, headers=headers)
    t = requests.get(file_url, stream=True, headers=headers)

    # Determine file name from url
    parsed_url = urlparse(file_url)
    file_name = os.path.basename(parsed_url.path)  # Get last part of path
    # Remove query strings
    if '?' in file_name:
        file_name = file_name.split('?')[0]

    print(f"{YELLOW}[{index}] Downloading: {file_name}")
    # Check if the file already exists
    if any(File.startswith(file_name) for File in os.listdir(".")):
        print(f"{YELLOW}[{index}] File {file_name} already exists. Skipping download.")
        return

    # Check if file_name already has extension
    allowed_extensions = [".jpeg", ".jp2", ".svg", ".mp4", ".mov", ".tiff", ".png", ".jpg", ".webp"]

    def has_allowed_extension(file_name):
        return any(file_name.lower().endswith(ext) for ext in allowed_extensions)

    if not has_allowed_extension(file_name):
	    # Detect file extension
        try:

            fs = t.raw.read(14)

            if fs.startswith(b"\xFF\xD8\xFF\xE0"):
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xDB"):
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xE0\x00\x10\x4A\x46x\49\x46\x00\x01"):
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xEE"):
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xE1"):
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\x66\x74\x79\x70\x69\x73\x6F\x6D"):
                file_name = f"{file_name}.mp4"
            elif fs.startswith(b"\x66\x74\x79\x70\x4D\x53\x4E\x56"):
                file_name = f"{file_name}.mp4"
            elif fs.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
                file_name = f"{file_name}.png"
            elif fs.startswith(b"\x49\x49\x2B\x00"):
                file_name = f"{file_name}.tiff"
            elif fs.startswith(b"\x4D\x4D\x00\x2B"):
                file_name = f"{file_name}.tiff"
            elif fs.startswith(b"\x49\x49\x2A\x00"):
                file_name = f"{file_name}.tiff"
            elif fs.startswith(b"\x4D\x4D\x00\x2A"):
                file_name = f"{file_name}.tiff"
            elif fs.startswith(b"\x66\x74\x79\x70\x71\x74\x20\x20"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x6D\x6F\x6F\x76"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x66\x72\x65\x65"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x6D\x64\x61\x74"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x77\x69\x64\x65"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x70\x6E\x6F\x74"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x70\x6E\x6F\x74"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x73\x6B\x69\x70"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b"\x00"):
                file_name = f"{file_name}.mov"
            elif fs.startswith(b'\x3c\x3f\x78\x6d\x6c\x20\x76\x65\x72\x73\x69\x6f\x6e'):
                file_name = f"{file_name}.svg"
            elif fs.startswith(b'\x52\x49\x46\x46'):
                print(f"{RED}RIFF container found. Guessing webp.")
                file_name = f"{file_name}.webp"
            elif fs.startswith(b"\xFF\xD8\xFF\xFE\x00\x10\x4C\x61\x76\x63\x36\x30"):
                print(f"{RED}File known to be encoded by lavc60. Guessing JPEG")
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xFE\x00\x10\x4C\x61\x76\x63\x35\x39"):
                print(f"{RED}File known to be encoded by lavc59. Guessing JPEG")
                file_name = f"{file_name}.jpeg"
            elif fs.startswith(b"\xFF\xD8\xFF\xFE\x00\x0F\x4C\x61\x76\x63\x36\x30"):
                print(f"{RED}File known to be encoded by lavc60. Guessing JPEG")
                file_name = f"{file_name}.jpeg"
            else: 
                if "SVG" in file_url:
                    print(f'{RED}Filetype could not be detected but "SVG" found in url. Guessing SVG')
                    file_name = f"{file_name}.svg"
                else:
                    print(f"{RED}Filetype unkown. File extension will not be added.")
        except Exception as e:
            print(f"{RED}Chunck read error: {e}")

    # Avoids being blocked by Snapchat servers
    sleep(0.3)

    # Download file
    try:
        if r.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"{YELLOW}Successfully downloaded {file_name}")
        else:
            print(f"{RED}Failed to download the media. Status code:", r.status_code)
    except Exception as e: 
        print(f"{RED}error downloading {file_name} exeption {e}")
        print("Downloading without stream")
        try:
            with open(file_name, "w") as f:
                content = requests.get(file_url, stream=False, headers=headers).content()
                f.write(content)
        except Exception as e:
            print(f"{RED}error downloading {file_name} exeption {e}")
    if timest == "":
        return
    elif timest == 0:
        return
    else:
        os.utime(file_name, (int(timest), int(timest)))

def main():
    start = time.perf_counter()

    profile_metadata()
    download_media()

    end = time.perf_counter()
    total = end - start

    print(f"\n\nTotal time: {total}")


if __name__ == "__main__":
    main()
