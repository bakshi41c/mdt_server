import bencode
import log as logpy
import json
from eth_account.messages import defunct_hash_message
from web3.auto import w3, Web3

log = logpy.get_logger('authentication.log')

class Auth:
    def __init__(self, config):
        self.config = config
        self.auth_key_path = config["auth"]["key_path"]
        self.block_chain_provider_url = config["smart_contract"]["bc_provider_url"]

        self.dee_id_abi_path = config["auth"]["deeid_abi_path"]

        with open(self.auth_key_path) as keyfile:
            encrypted_key = keyfile.read()
            keyfilejson = json.loads(encrypted_key)
            self.server_private_key = w3.eth.account.decrypt(encrypted_key, "leet") # TODO: Ask user for passphrase
            self.server_eth_address = keyfilejson['address']

        with open(self.dee_id_abi_path) as f:
            self.dee_id_abi = json.load(f)

        self.w3 = Web3(Web3.HTTPProvider(self.block_chain_provider_url))

    def sign_event(self, event_dict) -> dict:
        log.debug("Signing event: ")
        log.debug(event_dict)
        event_dict.pop("_id", None)
        event_dict['by'] = self.get_public_key_as_hex_string()
        msg = bencode.encode(event_dict).decode("utf-8")
        msg_hash = defunct_hash_message(text=msg)
        signed_message = w3.eth.account.signHash(msg_hash, private_key=self.server_private_key)
        event_dict["_id"] = signed_message['signature'].hex()
        return event_dict


    def get_sig_address_from_event(self, event_dict) -> bool:
        signature = event_dict.pop("_id", None)
        msg = bencode.encode(event_dict).decode("utf-8")
        return self.get_sig_address_from_signature(msg, signature)


    def get_sig_address_from_signature(self, msg, signature):
        msg_hash = defunct_hash_message(text=msg)
        eth_account_addr = w3.eth.account.recoverHash(msg_hash, signature=signature)
        return eth_account_addr.lower()


    def get_public_key_as_hex_string(self):
        return '0x' + self.server_eth_address


    def ethkey_in_deeid_contract(self, ethkey, deeid_contract):
        # TODO: [TEST]§1
        return True
        w3.eth.defaultAccount = self.server_eth_address
        dee_id_contract = w3.eth.contract(address=deeid_contract, abi=self.dee_id_abi,)
        len_k = dee_id_contract.functions.lenKeys().call()

        for i in range(0, len_k):
            key = dee_id_contract.functions.getKey(i).call()
            if str(key[1]) == str(ethkey):
                return True
        return False


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
