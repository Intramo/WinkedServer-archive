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

        self.isRight = False

class Session:
    def __init__(self) -> None:
        self.code = "".join([str(random.randint(0,9)) for i in range(7)])
        self.players:list[Player] = []

        self.questions = [{
            "type": "normal",
            "question": "Was macht Pittiplatsch bei den albanischen Rebellen?",
            "A":{
                "text": "Spielen",
                "correct": True
            },
            "B":{
                "text": "Im Kosovo einmarschieren",
                "correct": True
            },
            "C":{
                "text": "Zivilisten erschießen",
                "correct": True
            },
            "D":{
                "text": "Steuererklärung",
                "correct": True
            }
        },{
            "type": "truefalse",
            "question": "Ist Schnatterinchen ein Terrorist?",
            "isRight": True
        }]

        self.currentQuestionNum = 0
        self.currentQuestionState = -1
    
    async def next(self):
        self.currentQuestionState += 1 # 0 Question, 1 Answers, 2 Results, 3 Leaderboard
        if self.currentQuestionState > 3: 
            self.currentQuestionState = 0
            self.currentQuestionNum += 1
        if self.currentQuestionNum >= len(self.questions):
            for p in self.players:
                if not p.isHost:
                    await sendStateChangePacket(p, state="waiting")
                else:
                    await sendStateChangePacket(p, state="hostPodium")
            return

        self.q = self.questions[self.currentQuestionNum]
        
        if self.currentQuestionState == 0:
            for p in self.players:
                p.isRight = False
                p.answer = None
                if p.isHost:
                    await sendStateChangePacket(p, state = "hostQuestion" , question = self.q["question"])
            return

        if self.currentQuestionState == 1:
            for p in self.players:
                if self.q["type"] == "normal":
                    if p.isHost:
                        await sendStateChangePacket(p,
                            state = "hostAnswers" ,
                            question = self.q["question"],
                            a=self.q["A"]["text"],
                            b=self.q["B"]["text"],
                            c=self.q["C"]["text"],
                            d=self.q["D"]["text"]
                        )
                    else:
                        await sendStateChangePacket(p,
                            state = "answerNormal",
                            progress = f"{self.currentQuestionNum} von {len(self.questions)}"
                        )



                if self.q["type"] == "truefalse":
                    if p.isHost:
                        await sendStateChangePacket(p,
                            state = "hostAnswers" ,
                            question = self.q["question"]
                        )
                    else:
                        await sendStateChangePacket(p,
                            state = "answerNormal",
                            progress = f"{self.currentQuestionNum} von {len(self.questions)}"
                        )
            return

        if self.currentQuestionState == 2:
            for p in self.players:
                if not p.isHost:
                    if p.isRight:
                        p.points += 1000
                        p.answerStreak += 1
                        await sendStateChangePacket(p, state="playerCorrect")
                    else:
                        p.answerStreak = 0
                        await sendStateChangePacket(p, state="playerWrong")
                else:
                    await sendStateChangePacket(p, state="hostResults")
            return

        if self.currentQuestionState == 3:
            for p in self.players:
                if not p.isHost:
                    await sendStateChangePacket(p, state="waiting")
                else:
                    await sendStateChangePacket(p, state="hostLeaderboard")
            return

        


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
            
            if packettype.lower() == "next":
                s = [s for s in sessions if True in [p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                if p.isHost:
                    await s.next()
            
            if packettype.lower() == "answer":
                s = [s for s in sessions if True in [p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                btn = msg["answer"]
                
                if s.q["type"] == "normal":
                    p.isRight = s.q[btn]["correct"]
                
                if s.q["type"] == "truefalse":
                    p.isRight = (s.q["isRight"] and btn == "Y") or (not s.q["isRight"] and btn == "N")

            print(f"Received message from {websocket}: {message}")
    finally:
        del connections[websocket]

start_server = websockets.serve(handler, "localhost", 4348)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()