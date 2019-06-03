# C-meet backend
This is the repo for the backend of the c-meet system. <br>
The main components:
 - `rest_api_server.py` : handles all REST API requests from the frontend.
 - `meeting_server.py`: enables frontend clients to hold meetings.
 - `db.py`: database for meetings and events (using mongo)

## Quick setup
The quickest way to setup the system is by using docker containers.
The steps are as follows: <br>
1. Make sure you have [docker](https://docs.docker.com/install/) installed.
2. Go into docker directory, (`cd docker`)
3. Run `docker-compose up` (NOTE: This also sets up the [frontend](https://github.com/bakshi41c/mdt_web))
4. (Optional) The setup wont have any data. To generate sample data: <br>
    1. Open bash in the container with image 'bakshi41c/mdt_meeting_server', <br>
    (`docker exec -it container_id_here /bin/sh`)
    2. Run: `python gen_sample.py`
5. (Optional) The setup uses Ganache-CLI for a Ethereum test network.
But the server account doesn't have any money, as such it can't deploy any smart contracts.
**Follow topping up server eth account section**.

The front-end will be running on [http://localhost](http://localhost).

## Manual setup
If for any reason, docker is not an option, the system can be setup manually.
1. Make sure you have python 3.7+ installed.
2. Make sure you have [MongoDB](https://www.mongodb.com/) installed and running on port 27017 (can be configured).
3. Make sure you have [Ganache](https://truffleframework.com/ganache) installed.
4. Follow 'Setting up Ganache' section.
5. (Optional) Follow 'Topping up server eth account' section.
6. Run `pip install -r requirements.txt`.
7. (Optional) SET env variable `$MDT_SERVER_CONFIG` to use custom config (It uses config.json as default).
8. SET env variable `$PYTHONPATH` to this directory.
9. (Optional) Run `python gen_sample.py` to generate sample data.
10. Run `python meeting_server.py`.
11. Run `python rest_api_server.py`.

## Setting up Ganache
The system uses Ganache/Truffle for test Ethereum network. To setup Ganache: <br>
1. Download Ganache (GUI).
2. Create a workspace.
3. Go to settings, make sure the port is `8545` and network id is `5777`.

This can also be done using Ganache-CLI.

## Topping up server eth account
The server Ethereum account has no balanace at start, as such it cannot interact with the Ethereum network. To top up:
1. Install Metamask extension in Chrome or Firefox.
2. Connect Metamask to Ganache by setting up 'Custom RPC'. Ganache should be running on `localhost:8545`.
3. Import one of the accounts from Ganache (using the account's private key).
**If using docker:** the private key of all the test accounts should be printed in the console.
**If using Ganache GUI:** the private key is hidden under the key icon.
The test accounts should all have 100 ETH by default.
4. Import the server's account into Metamask, using the `sample_server_eth_key` JSON file (select import type as 'JSON file' rather than 'Private Key' in Metamask).
5. Transfer some (50 recommended) ETH from the Ganache test account to the server account.


## Docker
The docker images that are generated from this repository:
- `bakshi41c/mdt_rest_api_server` : [https://hub.docker.com/r/bakshi41c/mdt_rest_api_server](https://hub.docker.com/r/bakshi41c/mdt_rest_api_server)
- `bakshi41c/mdt_meeting_server` : [https://hub.docker.com/r/bakshi41c/mdt_meeting_server](https://hub.docker.com/r/bakshi41c/mdt_meeting_server)

New commits automatically generate new images.

## DeeID
The system utilises [DeeID Websocket server](https://github.com/deeid/websocket_server).
The default configuration uses the publicaly available server at: [ws://deeid.uksouth.azurecontainer.io:5678]()

The DeeID mobile app (which is required to sign in) can be obtained from: <br>
[https://github.com/sirvan3tr/OmneeMobileApp](https://github.com/sirvan3tr/OmneeMobileApp)


## Other tools

### Contract CLI
The contract CLI can be used to check and deploy smart contract without the web app. To use it, run `python tests/contract_cli.py [meeting_id]`

### Meeting CLI
The meeting CLI can be used to generate meeting events without the web app. To use it, run `python tests/meeting_cli.py [staff_deeid] [staff private_key]`
