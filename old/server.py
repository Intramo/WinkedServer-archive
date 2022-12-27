import asyncio, websockets, json, random, os


class Player:
    def __init__(self, s, name, host) -> None:
        self.socket = s
        self.name: str = name
        self.answerStreak: int = 0
        self.points: int = 0
        self.isHost: bool = host

        self.isRight = False


class Session:
    def __init__(self) -> None:
        self.code = "".join([str(random.randint(0, 9)) for i in range(7)])
        self.players: list[Player] = []

        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "quizes/starwars.json"), "r") as f:
            self.questions = json.load(f)["questions"]

        self.currentQuestionNum = 0
        self.currentQuestionState = -1

    async def next(self):
        self.currentQuestionState += 1  # 0 Question, 1 Answers, 2 Results, 3 Leaderboard
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
                    await sendStateChangePacket(p, state="hostQuestion", question=self.q["question"])
            return

        if self.currentQuestionState == 1:
            hasmedia = self.q["media"] != {}
            media = ""
            if hasmedia:
                mediatype = list(self.q["media"].keys())[0]
                mediasrc = self.q["media"][mediatype]
                if mediatype == "img":
                    media = f"<img src=\"{mediasrc}\"/>"

            for p in self.players:
                if self.q["type"] == "normal":
                    if p.isHost:
                        await sendStateChangePacket(p,
                                                    state="hostAnswersNormal",
                                                    question=self.q["question"],
                                                    duration=self.q["duration"],
                                                    a=self.q["A"]["text"],
                                                    b=self.q["B"]["text"],
                                                    c=self.q["C"]["text"],
                                                    d=self.q["D"]["text"],
                                                    media=media
                                                    )
                    else:
                        await sendStateChangePacket(p,
                                                    state="answerNormal",
                                                    progress=f"{self.currentQuestionNum} von {len(self.questions)}"
                                                    )

                if self.q["type"] == "truefalse":
                    if p.isHost:
                        await sendStateChangePacket(p,
                                                    state="hostAnswersTrueFalse",
                                                    duration=self.q["duration"],
                                                    question=self.q["question"],
                                                    media=media
                                                    )
                    else:
                        await sendStateChangePacket(p,
                                                    state="answerTrueFalse",
                                                    progress=f"{self.currentQuestionNum} von {len(self.questions)}"
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
                    if self.q["type"] == "normal":
                        await sendStateChangePacket(p,
                            state="hostResultsNormal",
                            question=self.q["question"],
                            a=self.q["A"]["text"],
                            b=self.q["B"]["text"],
                            c=self.q["C"]["text"],
                            d=self.q["D"]["text"],
                            amountRed=self.amountA,
                            amountBlue=self.amountB,
                            amountYellow=self.amountC,
                            amountGreen=self.amountD
                        )
                    if self.q["type"] == "truefalse":
                        await sendStateChangePacket(p,
                            state="hostResultsTrueFalse",
                            question=self.q["question"],
                            amountRed=self.amountN,
                            amountBlue=self.amountY
                        )
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


async def sendStateChangePacket(
        player: Player,
        state: str = "waiting",
        answerCorrect: bool = False,
        progress: int = 0,
        question: str = "",
        a: str = "",
        b: str = "",
        c: str = "",
        d: str = "",
        numQuestions: int = 0,
        duration: int = 0,
        amountRed: int = 0,
        amountBlue: int = 0,
        amountYellow: int = 0,
        amountGreen: int = 0,
        media = "<img src=\"assets/placeholder.jpg\">"
    ):
    await player.socket.send(json.dumps(
        {
            "packettype": "gamestate",
            "gameState": state,

            "playerAnswerStreak": player.answerStreak,
            "playerName": player.name,
            "playerPoints": player.points,
            "answerCorrect": answerCorrect,
            "progress": f"{str(progress)} von {str(numQuestions)}",
            "hostQuestionName": question if player.isHost else "",
            "hostOptionNameRed": a if player.isHost else "",
            "hostOptionNameBlue": b if player.isHost else "",
            "hostOptionNameYellow": c if player.isHost else "",
            "hostOptionNameGreen": d if player.isHost else "",
            "hostQuestionDuration": duration if player.isHost else 0,
            "hostAmountRed": amountRed if player.isHost else 0,
            "hostAmountBlue": amountBlue if player.isHost else 0,
            "hostAmountYellow": amountYellow if player.isHost else 0,
            "hostAmountGreen": amountGreen if player.isHost else 0,
            "hostMedia": media if player.isHost else "<img src=\"assets/placeholder.jpg\">"
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

                            if pl.isHost:
                                await sendStateChangePacket(pl, state="hostLobby")
                            if not pl.isHost:
                                await sendStateChangePacket(pl, state="waiting")
                                for p in s.players:
                                    if p.isHost:
                                        await p.socket.send(json.dumps({"packettype": "lobbyjoin", "name": pl.name}))

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
                btn = msg["answer"]

                if btn == "A": s.amountA += 1
                if btn == "B": s.amountB += 1
                if btn == "C": s.amountC += 1
                if btn == "D": s.amountD += 1
                if btn == "Y": s.amountY += 1
                if btn == "N": s.amountN += 1

                if s.q["type"] == "normal":
                    p.isRight = s.q[btn]["correct"]

                if s.q["type"] == "truefalse":
                    p.isRight = (s.q["isRight"] and btn == "Y") or (
                        not s.q["isRight"] and btn == "N")
    finally:
        del connections[websocket]

start_server = websockets.serve(handler, "localhost", 4348)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
