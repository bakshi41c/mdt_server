import hashlib
import bencode
import log as logpy
import web3
import json
from eth_account.messages import defunct_hash_message
from web3.auto import w3

server_private_key = None
server_eth_address = None

log = logpy.get_logger('authentication.log')
sample_server_eth_key_passphrase = 'leet'

with open('sample_server_eth_key') as keyfile:
    encrypted_key = keyfile.read()
    server_private_key = w3.eth.account.decrypt(encrypted_key, sample_server_eth_key_passphrase)
    keyfilejson = json.loads(encrypted_key)
    server_eth_address = keyfilejson['address']

def sign_event(event) -> dict:
    log.debug("Signing event: ")
    log.debug(event)
    event.pop("eventId", None)
    event['by'] = get_public_key_as_hex_string()
    msg = bencode.encode(event).decode("utf-8")
    msg_hash = defunct_hash_message(text=msg)
    signed_message = w3.eth.account.signHash(msg_hash, private_key=server_private_key)
    event["eventId"] = signed_message['signature'].hex()
    return event


def get_sig_address_from_event(event) -> bool:
    signature = event.pop("eventId", None)
    msg = bencode.encode(event).decode("utf-8")
    msg_hash = defunct_hash_message(text=msg)
    eth_account_addr = w3.eth.account.recoverHash(msg_hash, signature=signature)
    return eth_account_addr.lower()


def get_public_key_as_hex_string():
    return '0x' + server_eth_address

#
# ack_event_sample = {
#     "by": "",
#     "eventId": "",
#     "refEvent": "007a2cd2944e39a5b46747749c8d648354809273513d59d0c0d4414120174f8515b61b70eec21d",
#     "timestamp": 41654654021,
#     "meetingId": "da9ff03c5e0abea12c2f1dc09a5a58accdb51da1c58950ad974",
#     "type": "ack",
#     "content": {
#         "otp": "5123"
#     }
# }
#
# join_sample_event = {"timestamp":2814719824,"refEvent":"21823g2o3gno23ig2o3ign23g23","meetingId":"i32ht923hng2o3ign23oigh","type":"joinAck","by":"enwvmkmwlkevn","eventId":"0xe61abb0df4d1315e4c77261452c9c1cb55f112792177220a1dbe22ad460bd16d525f7ae1fac67d71159d4b64a213e297b604d921af9fb19bda131d007acaafda1b"}
# event_json = json.dumps(sign_event(ack_event_sample))
# print(event_json)
# print(verify_event(join_sample_event, '0x5266130E7fe890e04CC76A3dAf51cF046EEF00Ab'))
#
# #
# start_event_sample = {"by":"f8e9c51b4ec6f5a6fbf98fe7dc6919da76f0b0dc88f052155b5b01ab6a978a23375bd08b4bfed868eb1a3424607b951296f6900cff808d36843aeba693eac64f","meetingId":"ef69e5efdb993bc18cca0702a41d5b782f9a5d","timestamp":"96405406540","type":"start","room":"c7d7d2c04b60be4f75ce822d05a6eff90","content":{"otp":"4256"},"eventId":"61c0bf1b6f9e055b0d1671dc565a6df2250923120cae2b5f877012e7164a6b0daacb2ab50936e7448ec334cf81bf69304fda1f4e88160be7c5d1a40949089843"}
# print(verify_message(start_event_sample))

# print(vk.to_string().hex())
# # print(str(sk.to_string().hex()).__len__()*4)
# ack_event.pop("eventId", None)
# msg = str.encode(json.dumps(ack_event))
#
# signature = sk.sign(msg)
#
# ack_event["eventId"] = signature.hex()
#
# print(ack_event)
#
# # print(hashlib.sha1(msg).hexdigest())
# print(vk.verify(signature.fromhex(ack_event["eventId"]), msg, hashfunc=hashlib.sha256))
#
