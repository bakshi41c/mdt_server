from web3.auto import w3, Web3
import json

from model import Meeting
import log as logpy

log = logpy.get_logger('contract_helper')


class MeetingContractHelper:
    """
    Helper class to interface with the Meeting Contract
    """
    def __init__(self, config):
        self.config = config

        # Get the ETH Key
        self.auth_key_path = config["auth"]["key_path"]

        # Get Smart contract params
        self.block_chain_provider_url = config["smart_contract"]["bc_provider_url"]
        self.compiled_contract_path = config["smart_contract"]["meeting_contract_path"]
        self.chain_id = config["smart_contract"]["chain_id"]
        self.max_gas = config["smart_contract"]["max_gas"]

        # Get the private key from the keyfile
        with open(self.auth_key_path) as keyfile:
            encrypted_key = keyfile.read()
            keyfilejson = json.loads(encrypted_key)
            self.server_private_key = w3.eth.account.decrypt(encrypted_key, "leet") # TODO: Ask user for passphrase
            self.server_eth_address = keyfilejson['address']

        # Get the Meeting contract ABI from the ABI file
        with open(self.compiled_contract_path) as contract_file:
            contract_file_data = contract_file.read()
            contract_json = json.loads(contract_file_data)
            self.contract_abi = contract_json['abi']
            self.contract_bytecode = contract_json['bytecode']

        self.w3 = Web3(Web3.HTTPProvider(self.block_chain_provider_url))


    def new_meeting_contract(self, meeting : Meeting):
        """
        Deploys a new meeting contract
        :param meeting: the meeting object associated with contract
        :return: Ethereum address of the contract
        """
        contract = w3.eth.contract(abi=self.contract_abi, bytecode=self.contract_bytecode)
        nonce = w3.eth.getTransactionCount(w3.toChecksumAddress('0x' + self.server_eth_address))
        log.debug('Nonce: ' + str(nonce))
        staff_dee_ids = [Web3.toChecksumAddress(staff_dee_id) for staff_dee_id in meeting.staff]
        print(staff_dee_ids)
        contract_txn = contract.constructor(meeting.id, staff_dee_ids).buildTransaction({
            'nonce': nonce,
            'chainId': self.chain_id,
            'gas': 2000000
        })
        signed = w3.eth.account.signTransaction(contract_txn, private_key=self.server_private_key)
        contract_txn_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        log.debug('Waiting for contract to be mined...')
        tx_receipt = w3.eth.waitForTransactionReceipt(contract_txn_hash)
        return str(tx_receipt.contractAddress)


    def set_event_hash(self, meeting : Meeting, start_event_hash : str, end_event_hash : str):
        """
        Sets the Event Hash in the Meeting Contract
        :param meeting: the Meeting object associated with the contract
        :param start_event_hash: the id of START event
        :param end_event_hash: the id of ACK_END event
        :return: the TX reciept
        """
        mdt_meeting = w3.eth.contract(
            address=meeting.contract_id,
            abi=self.contract_abi,
        )
        nonce = w3.eth.getTransactionCount(w3.toChecksumAddress('0x' + self.server_eth_address))
        f_call_txn = mdt_meeting.functions.setEvents(start_event_hash, end_event_hash).buildTransaction({
            'nonce': nonce,
            'chainId': self.chain_id,
            'gas': 2000000
        })
        signed = w3.eth.account.signTransaction(f_call_txn, private_key=self.server_private_key)
        contract_txn_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
        print('Waiting for TX to be mined...')
        tx_receipt = w3.eth.waitForTransactionReceipt(contract_txn_hash)
        return tx_receipt
