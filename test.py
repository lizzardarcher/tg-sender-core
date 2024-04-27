import random
l = [1,2,3,4,5]
print(random.randint(1,20))
random.shuffle(l)
print(l)



from pyrogram import Client
client = Client(name='5520249502', api_id=9204378, api_hash='d557f412d36e5147cce94df6e6d4ea7f', phone_number='+79677098173',
                device_model="iPhone 11 Pro",
                system_version="16.1.2",
                app_version="11.2",
                lang_code="en")
client.start()
client.stop()