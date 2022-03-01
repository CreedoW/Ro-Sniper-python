import http
import requests
import threading
import os
from types import SimpleNamespace
import json
import random
import time
from dotenv import load_dotenv
load_dotenv(verbose=True)

ROBLOX_TOKEN = os.getenv('TOKEN')
THREADS = os.getenv('THREADS')
PROFIT = os.getenv('PROFIT')
MAXTOPAY = os.getenv('MAXTOPAY')
print(f"Loaded {THREADS}, {PROFIT}, {MAXTOPAY}")
Cookie_TOKEN = {'.ROBLOSECURITY': ROBLOX_TOKEN}
lock = threading.Lock()

Thread_Count = []

with open('proxy.txt') as f:
    proxies_list = [proxies_list.rstrip() for proxies_list in f]
# print(proxies_list)

def LimitedLinkFinder(Asset_ID):

    Req_Prdt_Inf = requests.get(f"https://api.roblox.com/marketplace/productinfo?assetId={Asset_ID}", cookies=Cookie_TOKEN)
    try:
        if Req_Prdt_Inf.json()["IsLimited"] != True:
            print("Given ID is not limited")
            return 0
        Asset_Type_ID = Req_Prdt_Inf.json()["AssetTypeId"]
    except:
        print("Wrong Limited ID or bad connection")
        return 0

    Req_Ownr_Inf = requests.get(f"https://inventory.roblox.com/v2/assets/{Asset_ID}/owners?sortOrder=Asc&limit=100", cookies=Cookie_TOKEN)

    for data in Req_Ownr_Inf.json()['data']:
        if data['owner'] == None:
            continue

        owner_id = data['owner']['id']
        print(f"cur {owner_id}")
        
        Req_Inv_Stus = requests.get(f"https://inventory.roblox.com/v1/users/{owner_id}/can-view-inventory")
        if Req_Inv_Stus.json()['canView'] == True:

            Req_Oln_Stus = requests.get(f"http://api.roblox.com/users/{owner_id}/onlinestatus")
            if int(Req_Oln_Stus.json()['LastOnline'][0:4]) < 2022: #Searching user who logged in before 2022 so that cache get more stable

                cursor = ""
                for a in range(100):
                    url = f"https://www.roblox.com/users/inventory/list-json?assetTypeId={Asset_Type_ID}&cursor={cursor}&itemsPerPage=10&userId={owner_id}"
                    Req_Catalog_API = requests.get(url)
                    i = 0
                    for x in Req_Catalog_API.json()['Data']['Items']:
                        if x['Item']['AssetId'] == int(Asset_ID):
                            return url, i, 1
                            
                        cursor = Req_Catalog_API.json()['Data']['nextPageCursor']
                        i += 1
                    
                    if cursor == None:
                        break

class XSRF_Worker(threading.Thread):
    

    def __init__(self, args, name=""):
        
        threading.Thread.__init__(self)
        self.name = name
        self.args = args

    def run(self):
        global xsrf_token
        while True:
            

            #Get XSRF Token for Purchases
            conn = http.client.HTTPSConnection("auth.roblox.com")
            conn.request("POST", "/v2/login", headers={"Cookie": f".ROBLOSECURITY={ROBLOX_TOKEN}"})
            resp = conn.getresponse()
            new_xsrf = resp.getheader("X-CSRF-TOKEN")
            data = resp.read()

            xsrf_token = new_xsrf
            # print(u_data)
            time.sleep(60)

class Count_Worker(threading.Thread):

    def __init__(self, args, name=""):
        
        threading.Thread.__init__(self)
        self.name = name
        self.args = args

    def run(self):
        global total_count
        total_count = 0
        global total_ratelimit
        total_ratelimit = 0
        while True:
            t30_count = total_count
            t30_limit = total_ratelimit
            time.sleep(300)
            print(f"Last 5 Min Checked {str(total_count - t30_count)}, Last 5 Min Error{str(total_ratelimit - t30_limit)}, Total Checks {str(total_count)}")



class Worker(threading.Thread):

    def __init__(self, args):
        
        threading.Thread.__init__(self)
        self.args = args

    def run(self):
        
        global Rap
        global xsrf_token
        global total_count
        global total_ratelimit
        proxyy = random.choice(proxies_list)
        proxyy = {
            'http': proxyy,
            'https': proxyy,
        }
        try:

            req_price = requests.get(self.args[1], proxies=proxyy, timeout=2)

            price = req_price.json()['Data']['Items'][int(self.args[2])]['Product']['PriceInRobux']

            total_count += 1
        except Exception as e:

            total_ratelimit += 1

            # print("Cache error or ratelimited", e)
            
            return

        try:
            if int(price) * (float(PROFIT) + 1) < int(Rap[self.args[0]]) * 0.7:
                if int(price) > int(MAXTOPAY):

                    return
                reseller = requests.get(url=f"https://economy.roblox.com/v1/assets/{self.args[0]}/resellers?cursor=&limit=10",cookies=Cookie_TOKEN)

                reseller = reseller.json()['data'][0]
                userAssetID = str(reseller["userAssetId"])
                sellerID = str(reseller["seller"]["id"])

                conn = http.client.HTTPSConnection("economy.roblox.com")

                conn.request(
                    method="POST",
                    url=f"/v1/purchases/products/{self.args[0]}",
                    body='{"expectedCurrency":1,"expectedPrice":%s,"expectedSellerId":%s,"userAssetId":%s}' % (str(price), sellerID, userAssetID),
                    headers={"Content-Type": "application/json", "Cookie": ".ROBLOSECURITY=%s" % str(ROBLOX_TOKEN), "X-CSRF-TOKEN": xsrf_token}
                )
                resp = conn.getresponse()
                data = resp.read()

                print(json.loads(data, object_hook=lambda d: SimpleNamespace(**d)))

                return

        except Exception as e:
            print(e)
    
if __name__ == '__main__':
    th = XSRF_Worker(name="XSRF_Worker_1", args=(None,))
    th.start()
    global Rap
    Rap = {}
    print("Ro-Sniper Python by Kon_UU")
    try:
        conn = http.client.HTTPSConnection("www.roblox.com")
        conn.request("GET", "/mobileapi/userinfo", headers={"Cookie": f".ROBLOSECURITY={ROBLOX_TOKEN}"})
        resp = conn.getresponse()
        data = resp.read()
        x = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
        print("Username: ", str(x.UserName), "Robux: ", str(x.RobuxBalance))
    except:
        print("Cookie error")
        time.sleep(5)
        exit(0)    
    i = input("(1) Caching, (2) Sniping")

    
    if i == "1":
        Asset_IDS = open("Limited_IDS.txt").readlines()
        for line in Asset_IDS:
            print(f"{line.strip()} Started to cache")
            try:
                x, y, z = LimitedLinkFinder(line.strip())
            except:
                print(f"{line.strip()} Failed")

            if z == 1:
                data = {"Asset_ID": line.strip(), "Url": x, "Content" : y}
                with open(f"caches/{line.strip()}.json","w+") as cache:
                    json.dump(data, cache)
                
    if i == "2":
        Asset_IDS = open("Limited_IDS.txt").readlines()
        ids = []
        for line in Asset_IDS:
            i = 0
            while i == 0:
                try:
                    Rap[line.strip()] = requests.get(f"https://economy.roblox.com/v1/assets/{line.strip()}/resale-data").json()['recentAveragePrice']
                    
                    i = 2
                except:
                    print("ratelimited! retrying after 10 sec")
                    time.sleep(10)

            ids.append(line.strip())
        
        th = Count_Worker(name="COUNT_Worker_1", args=(None,))
        th.start()
        while True:
            if threading.active_count() < int(THREADS) * len(ids):
                for x in ids:
                    # print(threading.active_count())
                    while threading.active_count() == int(THREADS) * len(ids):
                        None
                    with open(f'caches/{x}.json') as json_file:
                        data = json.load(json_file)
                        url, content = data['Url'], data['Content']
                    th = Worker(args=(x, url, content))
                    th.start()
