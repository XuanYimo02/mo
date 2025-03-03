# auto_get_xpath

根据提供的页面信息自动获取xpath

程序入口
main.py
修改 headers、cookies、web_datas
商品只存在一个价格，填入cur_price
商品breadlist为空，填入[]
其余字段为空，填入''
实例
headers = {
        "authority": "www.thehut.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7",
        "cache-control": "max-age=0",
        "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
cookies = {
        "chumewe_user": "19babe32-f89e-402f-821e-3ee670afd213",
        "locale_V6": "en_GB",
        "LPVID": "IwYzM5ZDBkNmEzYmI2YTRh",
        "emailReEngagementCookie": "newsletter-rejected",
        "actualOptanonConsent": "%2CC0003%2CC0002%2CC0001%2CC0004%2CC0005%2C",
        "_qubitTracker": "3062b8bc-f12b-44e5-adc8-51c136fc3338",
        "_gid": "GA1.2.924456776.1705990535",
        "qb_generic": ":Y009bkI:.thehut.com",
        "OptanonAlertBoxClosed": "2024-01-23T06:15:41.525Z",
        "_gcl_au": "1.1.340142373.1705996549",
        "_cs_c": "0",
        "JSESSIONID": "C6D129D5D4E0BA0631B1DAC8F4272B5F",
        "chumewe_sess": "b0fcb16c-4b2b-4d46-b142-b3865962c004",
        "csrf_token": "93994322249141622473",
        "NSC_mc_wtsw_efgbvmu_xfctsw_8010_F": "3744a3d0cefae6e79fcb32d2a8caacaf35b96ca2f0ccafc2c93d828b57f5b47b7899ef2e",
        "_cs_mk_ga": "0.6435618118404138_1706075192336",
        "gaVisitId": "id2r35q66akkc",
        "OTnoShow": "popup",
        "_ga_DDLHW2PLMW": "GS1.1.1706075192.2.0.1706075192.60.0.0",
        "_ga": "GA1.2.1608166038.1705990535",
        "_dc_gtm_UA-56952874-1": "1",
        "_dc_gtm_UA-59323-4": "1",
        "_cs_id": "38104f16-a9d5-aaec-99c9-c5f68c360a60.1705996548.2.1706075192.1706075192.1.1740160548859.1",
        "_cs_s": "1.0.0.1706076992552",
        "en_chosenSubsite_V6": "en",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Jan+24+2024+13%3A46%3A33+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=6.35.0&isIABGlobal=false&hosts=&consentId=ab21fa35-c078-44b9-aea5-b26847657da3&interactionCount=4&landingPath=NotLandingPage&AwaitingReconsent=false&groups=C0003%3A1%2CC0002%3A1%2CC0001%3A1%2CC0004%3A1%2CC0005%3A1&geolocation=CN%3BZJ",
        "qb_permanent": "3062b8bc-f12b-44e5-adc8-51c136fc3338:20:1:4:4:0::0:1:0:Blr1mI:BlsKQ7:A::::101.68.70.170:hangzhou:7393:china:CN:30.25:120.17:hangzhou:156087:zhejiang%20sheng:35618::::Y06AYaw:Y06AYav:0:0:0::0:0:.thehut.com:0",
        "qb_session": "1:1:5::0:Y06AYav:0:0:0:0:.thehut.com",
        "cto_bundle": "44ifcV9BRjIlMkJtSGlhcWxUSDhLc3BqN3J1b3pQOUpIa3lqOG9YMkRaQ0NRcWZLOEVxc3c1blFvVnVtblRqdVJkemdpMjBybFo0QWswNUNRQWRNZkNpY2p1YVZ0dlY5WjMlMkJCbnFxWmN5Yko5SWg3Vk11V0ZYNkxZJTJGMG43SG1mbU5URFdIOGluZURmYUxCbWJKZTJRaGRiZzIlMkY5USUzRCUzRA",
        "LPSID-64479670": "qof6BD01Q72kKQJF2sWJWg"
    }
web_datas = [
    {
        "url": "https://www.thehut.com/footwear/ugg-women-s-classic-ultra-mini-platform-suede-boots/15004352.html",
        "title": "UGG Women's Classic Ultra Mini Platform Suede Boots",
        "cur_price": "155.00",
        "ori_price": "",
        "img": "https://static.thcdn.com/images/large/webp//productimg/1600/1600/15004352-1005115948131058.jpg",
        "breadlist": [
            "Home"
        ],
        "brand": "UGG"
    },
    {
        "url": "https://www.thehut.com/bags/damson-madder-leopard-print-canvas-tote-bag/14979034.html",
        "title": 'Damson Madder Leopard-Print Canvas Tote Bag',
        "cur_price": "35.00",
        "ori_price": "",
        "img": "https://static.thcdn.com/images/large/webp//productimg/1600/1600/14979034-1565112848338623.jpg",
        "breadlist": [
            "Home"
        ],
        "brand": "Damson Madder"
    },
    {
        "url": "https://www.thehut.com/clothing/jakke-katie-printed-faux-fur-coat/14609071.html",
        "title": "Jakke Katie Printed Faux Fur Coat",
        "cur_price": "174.00",
        "ori_price": "289.00",
        "img": "https://static.thcdn.com/images/large/webp//productimg/1600/1600/14609071-1465049559043034.jpg",
        "breadlist": [
           "Home"
        ],
        "brand": "Jakke"
    },
    {
        "url": "https://www.thehut.com/clothing/aligne-julia-stretch-cotton-gabardine-maxi-trench-coat/14841992.html",
        "cookie": "",
        "title": "Aligne Julia Stretch-Cotton Gabardine Maxi Trench Coat",
        "cur_price": "175.00",
        "ori_price": "249.00",
        "price": "",
        "img": "https://static.thcdn.com/images/large/webp//productimg/1600/1600/14841992-8115069087160732.jpg",
        "breadlist": [
            "Home"
        ],
        "brand": "Aligne"
    },
    {
        "url": "https://www.thehut.com/clothing/barbour-international-northolt-showerproof-shell-jacket/14607513.html",
        "cookie": "",
        "title": "Barbour International Northolt Showerproof Shell Jacket",
        "cur_price": "105.00",
        "ori_price": "149.00",
        "price": "",
        "img": "https://static.thcdn.com/images/large/webp//productimg/1600/1600/14607513-7765061750228540.jpg",
        "breadlist": [
            "Home",  "Women's Designer Clothing",  "Women's Designer Coats & Jackets"
        ],
        "brand": "Barbour International"
    }
]