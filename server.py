import asyncio
import websockets
import json
import random

class Player:
    def __init__(self, s, name, host) -> None:
        self.socket = s
        self.name:str = name
        self.answerStreak:int = 0
        self.points:int = 0
        self.isHost:bool = host

class Session:
    def __init__(self) -> None:
        self.code = "".join([str(random.randint(0,9)) for i in range(7)])
        self.players:list[Player] = []
        self.questions = [{
            "type": "normal",
            "question": "Was macht Pittiplatsch bei den albanischen Rebellen?",
            "A":{
                "text": "Spielen",
                "corerect": True
            },
            "B":{
                "text": "Im Kosovo einmarschieren",
                "corerect": True
            },
            "C":{
                "text": "Zivilisten erschießen",
                "corerect": True
            },
            "D":{
                "text": "Steuererklärung",
                "corerect": True
            }
        }]
        self.currentQuestionNum = 0
        self.question = self.questions[self.currentQuestionNum]


connections = {}
sessions = [Session()]

print(sessions[0].code)

async def sendStateChangePacket(player: Player, state:str = "waiting", answerCorrect:bool = False, progress:int = 0, question:str = "", a:str = "", b:str = "", c:str = "", d:str = "", numQuestions:int = 0):
    await player.socket.send(json.dumps(
        {
            "packettype": "gamestate",
            "gameState": state,

            "playerAnswerStreak": player.answerStreak,
            "playerName": player.name,
            "playerPoints": player.points,
            "answerCorrect": answerCorrect,
            "progress": f"{str(progress)} von {str(numQuestions)}" ,
            "hostQuestionName": question if player.isHost else "",
            "hostOptionNameRed": a if player.isHost else "",
            "hostOptionNameBlue": b if player.isHost else "",
            "hostOptionNameYellow": c if player.isHost else "",
            "hostOptionNameGreen": d if player.isHost else "",
        }
    ))


async def handler(websocket, path):
    connections[websocket] = False
    try:
        async for message in websocket:
            msg = json.loads(message)
            packettype = msg["packettype"]

            if packettype.lower() == "joinrequest":
                sessionCode = msg["session"]
                name = msg["name"].strip()

                if not True in [s.code == sessionCode for s in sessions]:
                    await websocket.send(json.dumps({"packettype": "error", "message": "Ungültiger Sitzungscode"}))
                else:
                    if len(name) < 3:
                        await websocket.send(json.dumps({"packettype": "error", "message": "Ungültiger Name. Mindestens 3 Zeichen"}))
                    else:
                        if name.lower() in [n.name.lower() for n in [s for s in sessions if s.code == sessionCode][0].players]:
                            await websocket.send(json.dumps({"packettype": "error", "message": "Dieser Name wird bereits genutzt"}))
                        else:
                            s = [s for s in sessions if s.code == sessionCode][0]
                            pl = Player(websocket, name, len(s.players) == 0)
                            s.players.append(pl)

                            if pl.isHost: await sendStateChangePacket(pl, state="hostLobby")
                            if not pl.isHost:
                                await sendStateChangePacket(pl, state="waiting")
                                for p in s.players:
                                    if p.isHost:
                                        await p.socket.send(json.dumps({"packettype": "lobbyjoin", "name": pl.name}))

            print(f"Received message from {websocket}: {message}")
    finally:
        del connections[websocket]

start_server = websockets.serve(handler, "localhost", 4348)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()