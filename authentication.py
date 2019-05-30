import bencode
import log as logpy
import json
from eth_account.messages import defunct_hash_message
from web3.auto import w3, Web3

log = logpy.get_logger('authentication.log')


class Auth:
    def __init__(self, config):
        """
        Auth class for all authentication/singing and crypto needs
        :param config: config.Config object
        """
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
        """
        Cryptographically signs an Event
        :param event_dict: Event as a dictionary
        :return: signed Event as a dictionary
        """
        log.debug("Signing event: ")
        log.debug(event_dict)
        event_dict.pop("_id", None)
        event_dict['by'] = self.get_public_key_as_hex_string()
        msg = bencode.encode(event_dict).decode("utf-8")
        msg_hash = defunct_hash_message(text=msg)
        signed_message = w3.eth.account.signHash(msg_hash, private_key=self.server_private_key)
        event_dict["_id"] = signed_message['signature'].hex()
        return event_dict

    def get_sig_address_from_event(self, event_dict) -> str:
        """
        Gets the Ethereum address of the signature from an event
        :param event_dict: Event as a dictionary
        :return: Ethereum address as string
        """
        signature = event_dict.pop("_id", None)
        msg = bencode.encode(event_dict).decode("utf-8")
        return self.get_sig_address_from_signature(msg, signature)

    def get_sig_address_from_signature(self, msg, signature):
        """
        Gets the Ethereum address of a signature
        :param msg: Message as str
        :param signature: Signature as str
        :return: Ethereum address as str
        """
        msg_hash = defunct_hash_message(text=msg)
        eth_account_addr = w3.eth.account.recoverHash(msg_hash, signature=signature)
        return eth_account_addr.lower()

    def get_public_key_as_hex_string(self):
        return '0x' + self.server_eth_address

    def ethkey_in_deeid_contract(self, ethkey, deeid_contract):
        """
        Checks if Etehreum key is part of the Smart contract
        :param ethkey: Ethereum key that's being checked as str
        :param deeid_contract: Ethereum key for the DeeID contract
        :return: true if it included in the contract, false otherwise
        """
        # TODO: Test - Currently untested
        return True
        w3.eth.defaultAccount = self.server_eth_address
        dee_id_contract = w3.eth.contract(address=deeid_contract, abi=self.dee_id_abi,)
        len_k = dee_id_contract.functions.lenKeys().call()

        for i in range(0, len_k):
            key = dee_id_contract.functions.getKey(i).call()
            if str(key[1]) == str(ethkey):
                return True
        return False