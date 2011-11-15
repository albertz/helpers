import requests
from BeautifulSoup import BeautifulSoup
from time import sleep

s = requests.session()

username = ''
password = ''

print "CCC-Presale 28C3 Script by @sctan [https://github.com/szechuen/CCC-Presale]"

# Sign In

print "Accessing Sign In..."

while True:
    sign_in = s.get("https://presale.events.ccc.de/accounts/sign_in")
    if sign_in.ok: break
    print "Request Error - Retrying..."

sign_in_soup = BeautifulSoup(sign_in.content)

account_post = {}
for item in sign_in_soup.findAll("input", type="hidden"): account_post[item['name']] = item['value']
for item in sign_in_soup.findAll("input", type="submit"): account_post[item['name']] = item['value']
account_post['account[username]'] = username
account_post['account[password]'] = password

account_link = "https://presale.events.ccc.de" + sign_in_soup.find("form")['action']

# Account

print "Accessing Account..."

while True:
    account = s.post(account_link, data=account_post)
    if account.ok: break
    print "Request Error - Retrying..."

account_soup = BeautifulSoup(account.content)

ordered = False
page = account
soup = account_soup

while not ordered:

    post = {}
    for item in soup.findAll("input", type="hidden"): post[item['name']] = item['value']
    for item in soup.findAll("input", type="submit"): post[item['name']] = item['value']

    link = "https://presale.events.ccc.de" + soup.find("form")['action']

    while True:
        page = s.post(link, data=post)
        if page.ok: break
        print "Request Error - Retrying..."
    
    soup = BeautifulSoup(page.content)

    last = open("last.html", "w")
    last.write(soup.prettify())
    last.close()

    if soup.find(text=lambda(x): x.find("There are currently not enough tickets available") != -1): 
        print "Not Open - Sleeping before retrying..."
        sleep(1)
    else:
        print "Ordered :D"
        ordered = True
