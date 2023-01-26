import asyncio
import websockets
import json
import random
import os
import ssl
import pathlib
import time
import urllib.parse

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "profanity.blacklist"), "r") as f:
    blacklist: list = f.read().split("\n")

class SendPacket:
    async def error(websocket, key:str) -> None:
        await websocket.send(json.dumps({"packettype": "error", "key": key}))

    async def waiting(p) -> None:
        await p.socket.send(json.dumps({"packettype": "gameState", "gameState": "waiting"}))

    async def lobbyJoin(p, name: str) -> None:
        await p.socket.send(json.dumps({"packettype": "lobbyJoin", "name": name}))

    async def addAnswerCount(p) -> None:
        await p.socket.send(json.dumps({"packettype": "addAnswerCount"}))

    async def hostLobby(p, gameid: str, preloadImageURLS: list, preloadAudio: list) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostLobby",
            "gameid": gameid,
            "preload": {
                "images": preloadImageURLS,
                "audio": preloadAudio
            }
        }))

    async def playerAnswerNormal(p, name: str, buttonA: bool, buttonB: bool, buttonC: bool, buttonD: bool, points: int, progress: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerNormal",
            "name": name,
            "buttons": {
                "A": buttonA,
                "B": buttonB,
                "C": buttonC,
                "D": buttonD
            },
            "points": points,
            "progress": progress
        }))

    async def playerAnswerSelect(p, name: str, buttonA: bool, buttonB: bool, buttonC: bool, buttonD: bool, points: int, progress: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerSelect",
            "name": name,
            "buttons": {
                "A": buttonA,
                "B": buttonB,
                "C": buttonC,
                "D": buttonD
            },
            "points": points,
            "progress": progress
        }))

    async def playerAnswerTrueFalse(p, name: str, points: int, progress: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerTrueFalse",
            "name": name,
            "points": points,
            "progress": progress
        }))

    async def playerAnswerText(p, name: str, points: int, progress: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerAnswerText",
            "name": name,
            "points": points,
            "progress": progress
        }))

    async def playerResultWrong(p) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerResultWrong"
        }))

    async def playerResultCorrect(p, answerstreak: int, points: int) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerResultCorrect",
            "points": points,
            "answerstreak": answerstreak
        }))

    async def playerResultCorrectSelect(p, answerstreak: int, points: int, correctamount: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "playerResultCorrectSelect",
            "points": points,
            "answerstreak": answerstreak,
            "correctamount": correctamount
        }))

    async def hostQuestion(p, question: str, progress:str, type:str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostQuestion",
            "progress": progress,
            "type": type,
            "question": question
        }))

    async def hostAnswersNormal(p, question: str, duration: int, a: str, b: str, c: str, d: str, media: str) -> None:
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

    async def hostAnswersTrueFalse(p, question: str, duration: int, media: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostAnswersTrueFalse",
            "question": question,
            "duration": duration,
            "media": media
        }))

    async def hostAnswersText(p, question: str, duration: int, media: str) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostAnswersText",
            "question": question,
            "duration": duration,
            "media": media
        }))

    async def hostResultsNormal(
            p, question: str,
            aEnabled: bool, aText: str, aCorrect: bool, aAmount: int,
            bEnabled: bool, bText: str, bCorrect: bool, bAmount: int,
            cEnabled: bool, cText: str, cCorrect: bool, cAmount: int,
            dEnabled: bool, dText: str, dCorrect: bool, dAmount: int) -> None:

        answers = {}
        if aEnabled:
            answers["A"] = {"text": aText,
                            "correct": aCorrect, "amount": aAmount}
        if bEnabled:
            answers["B"] = {"text": bText,
                            "correct": bCorrect, "amount": bAmount}
        if cEnabled:
            answers["C"] = {"text": cText,
                            "correct": cCorrect, "amount": cAmount}
        if dEnabled:
            answers["D"] = {"text": dText,
                            "correct": dCorrect, "amount": dAmount}

        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostResultsNormal",
            "question": question,
            "answers": answers
        }))

    async def hostResultsTrueFalse(p, question: str, isRight: bool, trueAmount: int, falseAmount: int) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostResultsTrueFalse",
            "question": question,
            "isRight": isRight,
            "trueAmount": trueAmount,
            "falseAmount": falseAmount
        }))

    async def hostResultsText(p, question: str, correct: list, wrong: list) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostResultsText",
            "question": question,
            "correct": correct,
            "wrong": wrong
        }))

    async def hostPodium(p, p1name: str, p1points: int, p2name: str, p2points: int, p3name: str, p3points: int) -> None:
        await p.socket.send(json.dumps({
            "packettype": "gameState",
            "gameState": "hostPodium",
            "p1name": p1name,
            "p1points": p1points,
            "p2name": p2name,
            "p2points": p2points,
            "p3name": p3name,
            "p3points": p3points
        }))

class Player:
    def __init__(self, s, name, host) -> None:
        self.socket = s
        self.name: str = name
        self.answerStreak: int = 0
        self.points: int = 0
        self.isHost: bool = host
        self.isRight: bool = False
        self.rightAmount: int = 0

class Session:
    def __init__(self) -> None:
        doesCodeExist = True
        while doesCodeExist:
            self.code = "".join([str(random.randint(0, 9)) for i in range(7)])
            doesCodeExist = len(
                [s.code for s in sessions if s.code == self.code]) > 0

        self.players: list[Player] = []

        self.currentQuestionNum = 0
        self.currentQuestionState = -1

    async def next(self):
        self.currentQuestionState += 1  # 0 Question, 1 Answers, 2 Results
        if self.currentQuestionState > 2:
            self.currentQuestionState = 0
            self.currentQuestionNum += 1
        if self.currentQuestionNum >= len(self.questions):
            for p in self.players:
                if p.isHost:
                    p1name = ""
                    p1points = 0
                    p2name = ""
                    p2points = 0
                    p3name = ""
                    p3points = 0

                    sort = list(sorted(
                        [p for p in self.players if not p.isHost], key=lambda e: e.points, reverse=True))

                    if (len(sort) >= 1):
                        p1name = sort[0].name
                        p1points = sort[0].points

                    if (len(sort) >= 2):
                        p2name = sort[1].name
                        p2points = sort[1].points

                    if (len(sort) >= 3):
                        p3name = sort[2].name
                        p3points = sort[2].points

                    await SendPacket.hostPodium(p, p1name, p1points, p2name, p2points, p3name, p3points)
                else:
                    await SendPacket.waiting(p)
            return

        self.q: dict = self.questions[self.currentQuestionNum]

        if self.currentQuestionState == 0:
            self.amountA = 0
            self.amountB = 0
            self.amountC = 0
            self.amountD = 0
            self.amountY = 0
            self.amountN = 0
            self.wrongAnswers = []
            for p in self.players:
                p.isRight = False
                p.answer = None
                p.rightAmount = 0
                p.answerTimestamp = 0
                if p.isHost:
                    await SendPacket.hostQuestion(p, self.q["question"], f"{self.currentQuestionNum + 1} von {len(self.questions)}", self.q["type"])
                else:
                    await SendPacket.waiting(p)
            return

        if self.currentQuestionState == 1:
            hasmedia = self.q.get("media", {}) != {}
            media = ""
            if hasmedia:
                mediatype = list(self.q["media"].keys())[0]
                mediasrc = self.q["media"][mediatype]
                if mediatype == "img":
                    media = f"<img src=\"{mediasrc}\"/>"
                if mediatype == "yt":
                    media = f"""<iframe width="560" height="315" src="https://www.youtube.com/embed/{mediasrc.split('?v=')[1]}?controls=0&autoplay=1&modestbranding=1&disablekb=1&rel=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>"""
                if mediatype == "ytaudio":
                    media = f"""<iframe style="opacity:1%" width="560" height="315" src="https://www.youtube.com/embed/{mediasrc.split('?v=')[1]}?controls=0&autoplay=1&modestbranding=1&disablekb=1&rel=0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>"""
                if mediatype == "audio":
                    media = f"""<audio src="{mediasrc}" controls autoplay></audio>"""

            self.qt: float = time.time()

            for p in self.players:
                if self.q["type"].lower() == "select":
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
                        await SendPacket.playerAnswerSelect(
                            p,
                            p.name,
                            "A" in self.q.keys(),
                            "B" in self.q.keys(),
                            "C" in self.q.keys(),
                            "D" in self.q.keys(),
                            p.points,
                            f"{self.currentQuestionNum + 1} von {len(self.questions)}"
                        )

                if self.q["type"].lower() == "normal":
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
                            "D" in self.q.keys(),
                            p.points,
                            f"{self.currentQuestionNum + 1} von {len(self.questions)}"
                        )

                if self.q["type"].lower() == "truefalse":
                    if p.isHost:
                        await SendPacket.hostAnswersTrueFalse(p, self.q["question"], self.q["duration"], media)
                    else:
                        await SendPacket.playerAnswerTrueFalse(p, p.name, p.points, f"{self.currentQuestionNum + 1} von {len(self.questions)}")

                if self.q["type"].lower() == "text":
                    if p.isHost:
                        await SendPacket.hostAnswersText(p, self.q["question"], self.q["duration"], media)
                    else:
                        await SendPacket.playerAnswerText(p, p.name, p.points, f"{self.currentQuestionNum + 1} von {len(self.questions)}")
            return

        if self.currentQuestionState == 2:
            for p in self.players:
                if not p.isHost:
                    additionalpoints = int(
                        (1-(
                            (abs(p.answerTimestamp - self.qt) - p.socket.latency * 2) / self.q["duration"]
                        )) * (1000 + 50 * (p.answerStreak - 1))
                    )

                    p.answerStreak += 1
                    if p.rightAmount > 0:
                        total = self.q.get("A", {"correct": False})["correct"] + self.q.get("B", {"correct": False})[
                            "correct"] + self.q.get("C", {"correct": False})["correct"] + self.q.get("D", {"correct": False})["correct"]
                        p.points += additionalpoints * \
                            int(p.rightAmount / total)
                        await SendPacket.playerResultCorrectSelect(p, p.answerStreak, additionalpoints, str(p.rightAmount) + " von " + str(total) + " richtig beantwortet")
                    elif p.isRight:
                        p.points += additionalpoints
                        await SendPacket.playerResultCorrect(p, p.answerStreak, additionalpoints)
                    else:
                        p.answerStreak = 0
                        await SendPacket.playerResultWrong(p)
                else:
                    if self.q["type"].lower() == "normal" or self.q["type"].lower() == "select":
                        await SendPacket.hostResultsNormal(
                            p, self.q["question"],
                            "A" in self.q.keys(), self.q["A"]["text"] if "A" in self.q.keys(
                            ) else "", self.q["A"]["correct"] if "A" in self.q.keys() else "", self.amountA,
                            "B" in self.q.keys(), self.q["B"]["text"] if "B" in self.q.keys(
                            ) else "", self.q["B"]["correct"] if "B" in self.q.keys() else "", self.amountB,
                            "C" in self.q.keys(), self.q["C"]["text"] if "C" in self.q.keys(
                            ) else "", self.q["C"]["correct"] if "C" in self.q.keys() else "", self.amountC,
                            "D" in self.q.keys(), self.q["D"]["text"] if "D" in self.q.keys(
                            ) else "", self.q["D"]["correct"] if "D" in self.q.keys() else "", self.amountD
                        )
                    if self.q["type"].lower() == "truefalse":
                        await SendPacket.hostResultsTrueFalse(p, self.q["question"], self.q["isRight"], self.amountY, self.amountN)
                    if self.q["type"].lower() == "text":
                        await SendPacket.hostResultsText(p, self.q["question"], self.q["correct"], self.wrongAnswers)
            return

sessions = []

async def testQuiz(q: str):
    try:
        q = json.loads(q)
        a = q["questions"][0]
        for b in q["questions"]:
            if b["type"] == "text":
                a = b["question"].split(" ")
                a = b["correct"][0]
                a = b["duration"] + 1
                a = b["media"].keys()
            if b["type"] == "truefalse":
                a = b["question"].split(" ")
                a = not b["isRight"]
                a = b["duration"] + 1
                a = b["media"].keys()
            if b["type"] == "normal":
                a = b["question"].split(" ")
                a = b["media"].keys()
                a = b["duration"] + 1

        return True
    except Exception as e:
        return str(e)

async def checkName(name: str) -> str:
    for n in blacklist:
        for wordnum, word in enumerate(name.split(" ")):
            if n.lower() == word.lower():
                newWord = name.split(" ")
                newWord[wordnum] = newWord[wordnum][0] + \
                    "*" * len(newWord[wordnum][1:])
                return " ".join(newWord).strip()
    return name

async def handler(websocket, path):
    try:
        async for message in websocket:
            msg = json.loads(message)
            packettype = msg["packettype"]

            if packettype.lower() == "joinrequest":
                sessionCode = msg["session"]
                name = msg["name"].strip()

                if not True in [s.code == sessionCode for s in sessions]:
                    await SendPacket.error(websocket, "error.id.exist")

                else:
                    if len(name) < 3:
                         await SendPacket.error(websocket, "error.name.tooshort")
                    if len(name) > 16:
                         await SendPacket.error(websocket, "error.name.toolong")
                    else:
                        name = await checkName(name)
                        if name.lower() in [n.name.lower() for n in [s for s in sessions if s.code == sessionCode][0].players]:
                            await SendPacket.error(websocket, "error.name.exist")

                        else:
                            s: Session = [
                                s for s in sessions if s.code == sessionCode][0]
                            pl: Player = Player(websocket, name, False)
                            s.players.append(pl)
                            await SendPacket.waiting(pl)
                            for p in s.players:
                                if p.isHost:
                                    await SendPacket.lobbyJoin(p, pl.name)

                await websocket.ping()
            
            if packettype.lower() == "next":
                s = [s for s in sessions if True in [
                    p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                if p.isHost:
                    await s.next()

            if packettype.lower() == "kickplayer":
                s = [s for s in sessions if True in [
                    p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]
                if p.isHost:
                    k = [k for k in s.players if k.name.lower() == msg.get("name", "").lower()]
                    await k[0].socket.close()

            if packettype.lower() == "answer":
                s = [s for s in sessions if True in [
                    p.socket == websocket for p in s.players]][0]
                p = [p for p in s.players if p.socket == websocket][0]

                btn = msg.get("button", "")
                answer = msg.get("text", "")
                btns = msg.get("buttons", {"A": False, "B": False, "C": False, "D": False})

                if btn == "A" or btns["A"]:
                    s.amountA += 1
                if btn == "B" or btns["B"]:
                    s.amountB += 1
                if btn == "C" or btns["C"]:
                    s.amountC += 1
                if btn == "D" or btns["D"]:
                    s.amountD += 1
                if btn == "Y":
                    s.amountY += 1
                if btn == "N":
                    s.amountN += 1

                if s.q["type"].lower() == "normal":
                    p.isRight = s.q[btn]["correct"]
                    
                if s.q["type"].lower() == "select":
                    g = lambda b: s.q.get(b, {"correct": False})["correct"]
                    p.rightAmount = (g("A") and btns["A"]) + (g("B") and btns["B"]) + (g("C") and btns["C"]) + (g("D") and btns["D"])

                if s.q["type"].lower() == "truefalse":
                    p.isRight = (s.q["isRight"] and btn == "Y") or (
                        not s.q["isRight"] and btn == "N")

                if s.q["type"].lower() == "text":
                    p.isRight = len(
                        [option for option in s.q["correct"] if option.lower() == answer.lower()]) >= 1
                    if not p.isRight:
                        s.wrongAnswers.append(await checkName(answer))
                
                p.answerTimestamp = time.time()

                for pl in s.players:
                    if pl.isHost:
                        await SendPacket.addAnswerCount(pl)

            if packettype.lower() == "hostrequest":
                result = await testQuiz(msg["quiz"])
                if (result == True):
                    s: Session = Session()
                    s.questions = json.loads(msg["quiz"])["questions"]

                    if (msg["randomizeQuestions"]):
                        random.shuffle(s.questions)

                    if (msg["randomizeQuestions"]):
                        for qn, q in enumerate(s.questions):
                            if q["type"].lower() == "normal".lower():
                                options = []
                                if q.get("A", None) != None:
                                    options.append(q["A"])
                                    del q["A"]
                                if q.get("B", None) != None:
                                    options.append(q["B"])
                                    del q["B"]
                                if q.get("C", None) != None:
                                    options.append(q["C"])
                                    del q["C"]
                                if q.get("D", None) != None:
                                    options.append(q["D"])
                                    del q["D"]

                                letters = ["A", "B", "C", "D"]
                                random.shuffle(letters)
                                for i in range(len(options)):
                                    q[letters[i]] = options[i]

                    sessions.append(s)
                    pl: Player = Player(websocket, "Host", True)
                    s.players.append(pl)
                    await SendPacket.hostLobby(pl, s.code,
                        [question["media"]["img"] for question in s.questions if question.get("media", {}).get("img", None) != None],
                        [question["media"]["audio"] for question in s.questions if question.get("media", {}).get("audio", None) != None],
                    )
                else:
                    await websocket.send(json.dumps({"packettype": "error", "message": "Ungültiges Quiz: " + str(result)}))
    finally:
        s = [s for s in sessions if True in [
            p.socket == websocket for p in s.players]]
        if len(s) > 0:
            s = s[0]
            p = [p for p in s.players if p.socket == websocket][0]
            s.players.remove(p)
            if (len(s.players) == 0):
                sessions.remove(s)
                print("Deleted session " + s.code)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
localhost_pem = pathlib.Path(__file__).with_name("cert.pem")
ssl_context.load_cert_chain(localhost_pem)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 4348, ssl=ssl_context):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
