#!/usr/bin/python

import requests
from BeautifulSoup import BeautifulSoup
from time import sleep
import os, sys, traceback

secrets = eval(open(os.path.expanduser("~/Documents/secrets")).read())
username = secrets["28c3_username"]
password = secrets["28c3_password"]

s = requests.session(
    headers = {
        "Origin": "https://presale.events.ccc.de/",
        "User-Agent": "Mozilla/5.0",
        "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
    }
)

print "CCC-Presale 28C3 Script by @sctan [https://github.com/szechuen/CCC-Presale]"

# Sign In

print "Accessing Sign In..."

while True:
    try:
        sign_in = s.get("https://presale.events.ccc.de/accounts/sign_in")
        if sign_in.ok: break
    except KeyboardInterrupt:
        quit()
    except:
        traceback.print_exc()
    print "Request Error - Retrying getting sign in page..."

print "sign_in page url:", sign_in.url
sign_in_soup = BeautifulSoup(sign_in.content)

account_post = []
for item in sign_in_soup.findAll("input", type="hidden"):
    print "hidden", item
    account_post.append((item['name'], item['value']))
account_post.append(('account[username]', username))
account_post.append(('account[password]', password))
for item in sign_in_soup.findAll("input", type="submit"):
    print "submit", item
    account_post.append((item['name'], item['value']))

account_link = "https://presale.events.ccc.de" + sign_in_soup.find("form")['action']
print "account link:", account_link
print s.cookies
print account_post

class Foo: pass
account_p = Foo()
account_p.items = lambda: account_post

# Account

print "Accessing Account..."

while True:
    try:
        account = s.post(account_link, data=account_p,
                         headers = {
                            "Referer": sign_in.url,
                         },
                         allow_redirects = True
                         #return_response=False
                         )
        #account.send()
        #print account, account._enc_data, account.headers
        #account = account.response
        print account
        if account.ok:
            open("last_login.html", "w").write(account.content.encode("utf8"))
            account_soup = BeautifulSoup(account.content)
            if account_soup.find(text=lambda(x): x.find("Signed in successfully") != -1):
                break
            else:
                print "Could not login!"
                os._exit(1)
                sleep(1)
        print account
    except KeyboardInterrupt:
        quit()
    except:
        traceback.print_exc()        
    print "Request Error - Retrying login..."

ordered = False
page = account
soup = account_soup

while not ordered:

    post = {}
    for item in soup.findAll("input", type="hidden"): post[item['name']] = item['value']
    for item in soup.findAll("input", type="submit"): post[item['name']] = item['value']

    link = "https://presale.events.ccc.de" + soup.find("form")['action']
    print "Ordering ...", link
    while True:
        try:
            page = s.post(link, data=post, allow_redirects=True)
            print page
            if page.ok: break
        except KeyboardInterrupt:
            quit()
        except:
            traceback.print_exc()
        print "Request Error - Retrying to order..."
    
    soup = BeautifulSoup(page.content)

    last = open("last.html", "w")
    last.write(soup.prettify())
    last.close()

    if soup.find(text=lambda(x): x.find("There are currently not enough tickets available") != -1): 
        print "Not Open - Sleeping before retrying..."
        sleep(1)
    elif soup.find(text=lambda(x): x.find("Username (this is NOT your email address)") != -1 or x.find("Username (this is NOT your email address)") != -1):
        print "Error, not logged in anymore?"
        sleep(1)
    else:
        print "Ordered :D"
        ordered = True
