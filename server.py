import asyncio, websockets, json, random, os

class SendPacket:
    async def error(p, msg:str) -> None:
        await p.socket.send(json.dumps({"packettype": "error", "message": msg}))
    
    async def waiting(p) -> None:
        await p.socket.send(json.dumps({"packettype": "gameState", "gameState": "waiting"}))

    async def lobbyJoin(p, name:str) -> None:
        await p.socket.send(json.dumps({"packettype": "lobbyJoin", "name": name}))

    async def addAnswerCount(p) -> None:
        await p.socket.send(json.dumps({"packettype": "addAnswerCount"}))
    
    async def hostLobby(p, gameid:str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostLobby",
            "gameid": gameid
        }))
    
    async def playerAnswerNormal(p, name:str, buttonA:bool, buttonB:bool, buttonC:bool, buttonD:bool, points:int, progress:str, media:dict) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerNormal",
            "name": name,
            "buttons":{
                "A": buttonA,
                "B": buttonB,
                "C": buttonC,
                "D": buttonD
            },
            "points": points,
            "progress": progress,
            "media": media
        }))
    
    async def playerAnswerTrueFalse(p, name:str, points:int, progress:str, media:dict) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerNormal",
            "name": name,
            "points": points,
            "progress": progress,
            "media": media
        }))

    async def playerResultWrong(p) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerResultWrong"
        }))
    
    async def playerResultCorrect(p, answerstreak:int) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerResultCorrect",
            "answerstreak": answerstreak
        }))
    
    async def hostQuestion(p, question:str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostQuestion",
            "question": question
        }))
    
    async def hostAnswersNormal(p, question:str, duration:int, a:str, b:str, c:str, d:str, media:str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostAnswersNormal",
            "question": question,
            "duration": duration,
            "answers": {
                "A": a,
                "B": b,
                "C": c,
                "D": d
            },
            "media": media
        }))
    
    async def hostAnswersTrueFalse(p, question:str, duration:int, media:str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostAnswersNormal",
            "question": question,
            "duration": duration,
            "media": media
        }))
    
    async def hostResultsNormal(
        p, question:str,
        aEnabled:bool, aText:str, aCorrect:bool, aAmount:int,
        bEnabled:bool, bText:str, bCorrect:bool, bAmount:int,
        cEnabled:bool, cText:str, cCorrect:bool, cAmount:int,
        dEnabled:bool, dText:str, dCorrect:bool, dAmount:int) -> None:

        answers = {}
        if aEnabled: answers["A"] = {"text": aText, "correct": aCorrect, "amount": aAmount}
        if bEnabled: answers["B"] = {"text": bText, "correct": bCorrect, "amount": bAmount}
        if cEnabled: answers["C"] = {"text": cText, "correct": cCorrect, "amount": cAmount}
        if dEnabled: answers["D"] = {"text": dText, "correct": dCorrect, "amount": dAmount}

        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostResultsNormal",
            "question": question,
            "answers": answers
        }))
    
    async def hostResultsTrueFalse(p, question:str, isRight:bool, trueAmount:int, falseAmount:int) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostResultsTrueFalse",
            "question": question,
            "isRight": isRight,
            "trueAmount": trueAmount,
            "falseAmount": falseAmount
        }))

class Player:
    def __init__(self, s, name, host) -> None:
        self.socket = s
        self.name: str = name
        self.answerStreak: int = 0
        self.points: int = 0
        self.isHost: bool = host
        self.isRight: bool = False

class Session:
    def __init__(self) -> None:
        self.code = "".join([str(random.randint(0, 9)) for i in range(7)])
        self.players: list[Player] = []

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "quizes/starwars.json"), "r") as f:
            self.questions = json.load(f)["questions"]

        self.currentQuestionNum = 0
        self.currentQuestionState = -1
    
    async def next(self):
        self.currentQuestionState += 1  # 0 Question, 1 Answers, 2 Results
        if self.currentQuestionState > 2:
            self.currentQuestionState = 0
            self.currentQuestionNum += 1
        if self.currentQuestionNum >= len(self.questions):
            for p in self.players:
                await SendPacket.waiting(p)
            return

        self.q:dict = self.questions[self.currentQuestionNum]

        if self.currentQuestionState == 0:
            self.amountA = 0
            self.amountB = 0
            self.amountC = 0
            self.amountD = 0
            self.amountY = 0
            self.amountN = 0
            for p in self.players:
                p.isRight = False
                p.answer = None
                if p.isHost:
                    await SendPacket.hostQuestion(p, self.q["question"])
            return

        if self.currentQuestionState == 1:
            hasmedia = self.q.get("media", {}) != {}
            media = f"<h1>{self.q['question']}</h1>"
            if hasmedia:
                mediatype = list(self.q["media"].keys())[0]
                mediasrc = self.q["media"][mediatype]
                if mediatype == "img":
                    media = f"<img src=\"{mediasrc}\"/>"

            for p in self.players:
                if self.q["type"] == "normal":
                    if p.isHost:
                        await SendPacket.hostAnswersNormal(
                            p,
                            self.q["question"],
                            self.q["duration"],
                            self.q["A"]["text"] if "A" in self.q.keys() else "",
                            self.q["B"]["text"] if "B" in self.q.keys() else "",
                            self.q["C"]["text"] if "C" in self.q.keys() else "",
                            self.q["D"]["text"] if "D" in self.q.keys() else "",
                            media
                        )
                    else:
                        await SendPacket.playerAnswerNormal(
                            p,
                            p.name,
                            "A" in self.q.keys(),
                            "B" in self.q.keys(),
                            "C" in self.q.keys(),
                            "D" in self.q .keys(),
                            p.points,
                            f"{self.currentQuestionNum} von {len(self.questions)}",
                            media
                        )
                if self.q["type"] == "truefalse":
                    if p.isHost: await SendPacket.hostAnswersTrueFalse(p, self.q["question"], self.q["question"], media)
                    else: await SendPacket.playerAnswerTrueFalse(p, p.name, p.points, f"{self.currentQuestionNum} von {len(self.questions)}", media)
            return

        if self.currentQuestionState == 2:
            for p in self.players:
                if not p.isHost:
                    if p.isRight:
                        p.points += 1000
                        p.answerStreak += 1
                        await SendPacket.playerResultCorrect(p, p.answerStreak)
                    else:
                        p.answerStreak = 0
                        await SendPacket.playerResultWrong(p)
                else:
                    if self.q["type"] == "normal":
                        await SendPacket.hostResultsNormal(
                            p, self.q["question"],
                            "A" in self.q.keys(), self.q["A"]["text"] if "A" in self.q.keys() else "", self.q["A"]["correct"] if "A" in self.q.keys() else "", self.amountA,
                            "B" in self.q.keys(), self.q["B"]["text"] if "B" in self.q.keys() else "", self.q["B"]["correct"] if "B" in self.q.keys() else "", self.amountB,
                            "C" in self.q.keys(), self.q["C"]["text"] if "C" in self.q.keys() else "", self.q["C"]["correct"] if "C" in self.q.keys() else "", self.amountC,
                            "D" in self.q.keys(), self.q["D"]["text"] if "D" in self.q.keys() else "", self.q["D"]["correct"] if "D" in self.q.keys() else "", self.amountD
                        )
                    if self.q["type"] == "truefalse":
                        await SendPacket.hostResultsTrueFalse(p, self.q["question"], self.q["isRight"], self.amountY, self.amountN)
            return

connections = {}
sessions = [Session()]

print(sessions[0].code)








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

                            if pl.isHost:
                                await SendPacket.hostLobby(pl, s.code)
                            if not pl.isHost:
                                await SendPacket.waiting(pl)
                                for p in s.players:
                                    if p.isHost:
                                        await SendPacket.lobbyJoin(p, pl.name)

            if packettype.lower() == "next":
                s = [s for s in sessions if True in [
                    p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                if p.isHost:
                    await s.next()

            if packettype.lower() == "answer":
                s = [s for s in sessions if True in [
                    p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                btn = msg["button"]

                if btn == "A": s.amountA += 1
                if btn == "B": s.amountB += 1
                if btn == "C": s.amountC += 1
                if btn == "D": s.amountD += 1
                if btn == "Y": s.amountY += 1
                if btn == "N": s.amountN += 1

                if s.q["type"] == "normal":
                    p.isRight = s.q[btn]["correct"]

                if s.q["type"] == "truefalse":
                    p.isRight = (s.q["isRight"] and btn == "Y") or (not s.q["isRight"] and btn == "N")
                
                for pl in s.players:
                    if pl.isHost:
                        await SendPacket.addAnswerCount(pl)
    finally:
        del connections[websocket]

start_server = websockets.serve(handler, "localhost", 4348)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()