#!/usr/bin/env python
'''
 Author: Sirvan Almasi @ Imperial College London
 Modified by: Shubham Bakshi
'''

import asyncio, websockets
import datetime
import random, string, json
from deeid.almasFFS import almasFFS

sockets = {}
almasFFSSocket = {}
serverIP = '127.0.0.1'
serverPort = 5678
print('Starting socket server....')
print('Running on http://' + str(serverIP) + ':' + str(serverPort))

# Number of rounds for the Fiat-Shamir Protocol
almasFFSRounds = 10


def uniqueID(size=12, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


async def sendUser(data):
    print("Sending User: ")
    print(data)
    if sockets[data['host']]:
        sigJSON = json.dumps({'type': 'signature', 'signature': data['signature']})
        await sockets[data['host']].send(sigJSON)


async def almasFFSSendJson(round, step, data, websocket):
    expJSON = json.dumps({'type': 'almasFFS', 'round': round, 'rnds': almasFFSRounds, 'step': step, 'data': data})
    await websocket.send(expJSON)


async def almasFFSHandler(data, websocket):
    v = almasFFSSocket[id(websocket)]['v']
    n = almasFFSSocket[id(websocket)]['n']
    e = almasFFSSocket[id(websocket)]['e']
    x = almasFFSSocket[id(websocket)]['x']
    rnd = almasFFSSocket[id(websocket)]['rnd']

    if (data['step'] == 0):
        # Initial setup, to calculate the users
        #   public key from the global function
        if (rnd < 1):
            I = str(data['data']['I'])
            j = data['data']['j']
            newN = int(data['data']['n'])
            almasFFSSocket[id(websocket)]['n'] = newN
            user = almasFFS(I, j, newN)
            almasFFSSocket[id(websocket)]['v'] = user.getPubKeys()

        almasFFSSocket[id(websocket)]['rnd'] += 1
        almasFFSSocket[id(websocket)]['x'] = 0
        almasFFSSocket[id(websocket)]['e'] = []

        await almasFFSSendJson(rnd + 1, 1, '', websocket)

    elif (data['step'] == 1):
        # Get and save x
        almasFFSSocket[id(websocket)]['x'] = int(data['data'])
        # Send random bits
        for i in range(0, len(v)):
            e.append(random.randint(0, 1))
        await almasFFSSendJson(rnd, 2, e, websocket)
        almasFFSSocket[id(websocket)]['e'] = e

    elif (data['step'] == 3):
        # Step 3, get y
        expected_x = int(data['data']) ** 2 % n
        for i in range(0, len(e)):
            if e[i] == 1:
                expected_x *= v[i]
        expected_x = expected_x % n

        # Step 4: Get the result
        result = 0
        if (expected_x == x) or (expected_x == (-x % n)):
            print("Challenge correctly completed!")
            await almasFFSSendJson(rnd, 4, 'Pass', websocket)
        else:
            print("Failure in challenge")
            almasFFSSocket[id(websocket)]['fails'] += 1
            await almasFFSSendJson(rnd, 4, 'Fail', websocket)

        if (almasFFSSocket[id(websocket)]['rnd'] == almasFFSRounds):
            print('Fails: ' + str(almasFFSSocket[id(websocket)]['fails']))


async def almasFFSMobileHandler(data, websocket):
    socketID = int(data['forID'])
    v = almasFFSSocket[socketID]['v']
    n = almasFFSSocket[socketID]['n']
    e = almasFFSSocket[socketID]['e']
    x = almasFFSSocket[socketID]['x']
    rnd = almasFFSSocket[socketID]['rnd']

    if (data['step'] == 0):
        # Initial setup, to calculate the users
        #   public key from the global function
        if (rnd < 1):
            I = str(data['data']['I'])
            j = data['data']['j']
            newN = int(data['data']['n'])
            almasFFSSocket[socketID]['n'] = newN
            user = almasFFS(I, j, newN)
            almasFFSSocket[socketID]['v'] = user.getPubKeys()

        almasFFSSocket[socketID]['rnd'] += 1
        almasFFSSocket[socketID]['x'] = 0
        almasFFSSocket[socketID]['e'] = []

        await almasFFSSendJson(rnd + 1, 1, '', websocket)

    elif (data['step'] == 1):
        # Get and save x
        almasFFSSocket[socketID]['x'] = int(data['data'])
        # Send random bits
        for i in range(0, len(v)):
            e.append(random.randint(0, 1))
        await almasFFSSendJson(rnd, 2, e, websocket)
        almasFFSSocket[socketID]['e'] = e

    elif (data['step'] == 3):
        # Step 3, get y
        expected_x = int(data['data']) ** 2 % n
        for i in range(0, len(e)):
            if e[i] == 1:
                expected_x *= v[i]
        expected_x = expected_x % n

        # Step 4: Get the result
        result = 0
        if (expected_x == x) or (expected_x == (-x % n)):
            print("Challenge correctly completed!")
            await almasFFSSendJson(rnd, 4, 'Pass', websocket)
        else:
            print("Failure in challenge")
            almasFFSSocket[socketID]['fails'] += 1
            await almasFFSSendJson(rnd, 4, 'Fail', websocket)

        if (almasFFSSocket[socketID]['rnd'] == almasFFSRounds):
            fails = int(almasFFSSocket[socketID]['fails'])
            print('### Fails: ' + str(fails))
            finalResult = ''
            if (fails == 0):
                finalResult = 'Pass'
            else:
                finalResult = 'Fail'
            await almasFFSSendJson(rnd, 4, finalResult, almasFFSSocket[socketID]['sock'])


async def main(websocket, path):
    uID = uniqueID()  # a unique id for connection
    sockets[uID] = websocket
    almasFFSSocket[id(websocket)] = {
        'sock': websocket,
        'uID': uID,
        'v': [],
        'n': 0,
        'e': [],
        'x': 0,
        'rnd': 0,
        'fails': 0,
        'almasFFS': 0,
    }

    socketID = id(websocket)
    print(almasFFSSocket[socketID])

    uIDJson = json.dumps({'type': 'uID', 'uID': uID})
    await websocket.send(uIDJson)

    almasFFSID = json.dumps({'type': 'uID', 'uID': id(websocket)})
    await websocket.send(almasFFSID)

    for key, val in sockets.items():
        print(key, "=>", val)

    try:
        async for message in websocket:
            print(message)
            data = json.loads(message)
            for key, val in sockets.items():
                print(key, "=>", val)

            # if its a login attempt
            if (data['type'] == 'loginSig'):
                await sendUser(data)

            if (data['type'] == 'almasFFS'):
                await almasFFSHandler(data, websocket)

            elif (data['type'] == 'almasFFSMobile'):
                await almasFFSMobileHandler(data, websocket)

    finally:
        del sockets[uID]
        del almasFFSSocket[id(websocket)]


start_server = websockets.serve(main, serverIP, serverPort)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()