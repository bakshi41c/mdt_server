import hashlib
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import bencode
import log as logpy


sk = SigningKey.generate(curve=SECP256k1, hashfunc=hashlib.sha256)
vk = sk.get_verifying_key()

log = logpy.get_logger('authentication.log')


def sign_event(event) -> dict:
    log.debug("Signing event: ")
    log.debug(event)
    event.pop("eventId", None)
    msg = bencode.encode(event)
    signature = sk.sign(msg)
    event["eventId"] = signature.hex()
    return event


def verify_event(event) -> bool:
    signature = event.pop("eventId", None)
    # print(signature)
    pub_key = VerifyingKey.from_string(bytes.fromhex(event["by"]), curve=SECP256k1, hashfunc=hashlib.sha256)

    #  We need to encode the JSON object with Bencode. Using jsonify/json.dumps() doesnt guarantee any format
    #  such as the white-spacing, order of keys etc.
    msg = bencode.encode(event)
    # print(hashlib.sha256(msg).hexdigest())
    return pub_key.verify(bytes.fromhex(signature), msg, hashfunc=hashlib.sha256)


def get_public_key_as_string():
    return vk.to_string().hex()

#
# ack_event_sample = {
#     "by": get_public_key_as_string(),
#     "eventId": "",
#     "refEvent": "007a2cd2944e39a5b46747749c8d648354809273513d59d0c0d4414120174f8515b61b70eec21d",
#     "timestamp": "01654654021",
#     "meetingId": "da9ff03c5e0abea12c2f1dc09a5a58accdb51da1c58950ad974",
#     "room": "da9ff03c5e0abea12c2f1dc09a5a58accdb51da1c58950ad974",
#     "type": "ack",
#     "content": {
#         "otp": "5123"
#     }
# }
#
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
