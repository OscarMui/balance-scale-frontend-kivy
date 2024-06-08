import asyncio
import random
import uuid

from common.constants import BOT_NICKNAMES, DEAD_LIMIT, DIGEST_TIME_MS, PARTICIPANTS_PER_GAME, ROUND_INFO_DIGEST_TIME_MS, ROUND_LIMIT, ROUND_TIME_MS, ROUND_ZERO_DIGEST_TIME_MS, SERVER_URL, WSS_URL, CLIENT_VERSION
from common.now import now
from common.socket import Socket

# We always assert that we occupy position 0 of the participants list
class SoloGame:
    nickname = None
    participants = None
    roundNumber = 1

    def __init__(self, qGame, qApp, nickname):
        self.qGame = qGame
        self.qApp = qApp
        self.nickname = nickname


    async def play(self):
        try:
            msg = {
                "event": "serverConnected",
                "participantsCount": PARTICIPANTS_PER_GAME,
                "participantsPerGame": PARTICIPANTS_PER_GAME,
            }

            self.qApp.put_nowait(msg)

            print("finished sending serverConnected event",msg)

            # export interface ParticipantInfo {
            #     id: string, 
            #     nickname: string,
            #     score: number,
            #     isDead: boolean,
            #     isBot: boolean,
            # }

            # construct participants info
            startingNickname = random.randint(0,len(BOT_NICKNAMES))
            self.participants = [
                { #ourselves
                    "id": uuid.uuid4(),
                    "nickname": self.nickname + " (YOU)",
                    "isBot": False, 
                    "score": 0,
                    "isDead": False,
                },
                *[{
                    "id": uuid.uuid4(),
                    "nickname": BOT_NICKNAMES[(startingNickname+i)%len(BOT_NICKNAMES)],
                    "isBot": True,
                    "score": 0,
                    "isDead": False,
                } for i in range(4)]
            ]

            # Show all 5 participants found in the join room screen, with their names

            # export interface GameStart extends GameEvent {
            #     event: "gameStart",
            #     participants: ParticipantInfo[],
            #     round: number,
            #     roundStartTime: number,
            #     roundEndTime: number,
            #     gameEnded: boolean,
            #     aliveCount: number,
            # }

            # To accomodate these changes made in onlineGame after receiving the gameEvent, we added (YOU) after the nickname of the actual human player
            # and we will also have the "us" attribute in the gameInfo/ msg
            # ps = event["participants"]
            # p = list(filter(lambda p: p["id"]==pid,ps))[0]
            # p["nickname"] = p["nickname"] + " (YOU)"
            # event["us"] = p
            # event["roundStartTime"] += now()
            # event["roundEndTime"] += now()

            msg = {
                "event": "gameStart",
                "participants": self.participants,
                "round": self.roundNumber,
                "roundStartTime": ROUND_ZERO_DIGEST_TIME_MS + now(),
                "roundEndTime": ROUND_ZERO_DIGEST_TIME_MS + ROUND_TIME_MS + now(),
                "gameEnded": False,
                "aliveCount": self.__getAliveCount(),
                "us": self.participants[0],
                "mode": "solo",
            }

            # send gameStart event to app
            self.qApp.put_nowait(msg)

            # The screen will wait until it is roundStartTime to switch to the main game screen
            
            

            while not self.__isEnded() and self.roundNumber < ROUND_LIMIT:
                # get events from the UI (if any)
                event = await self.qGame.get() 
                while(event["event"] != "submitGuess"):
                        if(event["event"] == "quitGame"): # players can quit the offline game at anypoint
                            return
                assert(event["event"] == "submitGuess")
                
                # generate guesses (reqs)
                reqs = [{ #the human
                    "guess": event["guess"],
                    "id": self.participants[0]["id"]
                },*[{ #bots
                    "guess": self.__botGuess(),
                    "id": participant["id"]
                } for participant in filter(lambda x: not x["isDead"],self.participants[1:])]]

                assert(len(reqs)==self.__getAliveCount())
                
                # basically copying code from backend at this point
                # calculate targets
                target = sum(map(lambda x: x["guess"],reqs))/len(reqs) * 0.8

                calDiff = lambda x: abs(target-x)

                winners = [] # ids of winners
                winnersDiff = None
                justAppliedRules = set()
                justDiedParticipants = []

                # check winners
                if(len(reqs)==2 and reqs[0]["guess"]==0 and reqs[1]["guess"]==100):
                    winners = [reqs[1]["id"]]
                    justAppliedRules.add(2)
                elif(len(reqs)==2 and reqs[0]["guess"]==100 and reqs[1]["guess"]==0):
                    winners = [reqs[0]["id"]]
                    justAppliedRules.add(2)
                else: 
                    for i in range(len(reqs)):
                        req = reqs[i]
                        # duplicates
                        if len(reqs) <= 4:
                            if len(list(filter(lambda x: x["guess"] == req["guess"],reqs)))>1:
                                justAppliedRules.add(4)
                        
                        diff = calDiff(req["guess"])
                        if(winnersDiff==None or diff < winnersDiff):
                            winners = [req["id"]]
                            winnersDiff = diff
                        elif(winnersDiff == diff):
                            winners.append(req["id"])
                
                
                    for i in range(len(reqs)):
                        req = reqs[i]

                        # get corresponding participant
                        p = list(filter(lambda x: x["id"] == req["id"],self.participants))[0]

                        # if alive and not win: -1 score
                        if(p["id"] not in winners):
                            if len(reqs) <= 3 and winnersDiff and winnersDiff <= 0.5:
                                # rule 3
                                if self.__changeScore(p,-2):
                                    justDiedParticipants.append({
                                        "id": p["id"],
                                        "reason": "deadLimit",
                                    })
                                justAppliedRules.add(3)
                            else:
                                if self.__changeScore(p,-1):
                                    justDiedParticipants.append({
                                        "id": p["id"],
                                        "reason": "deadLimit",
                                    })
                        
                    participantsGuess = list(map(lambda p: {
                        "guess": list(filter(lambda r: r["id"] == p["id"],reqs))[0]["guess"] if len(list(filter(lambda r: r["id"] == p["id"],reqs))) > 0 else None,
                        **p
                    },self.participants))
                    
                    self.roundNumber+=1
                    
                    msg = {
                        "event": "gameInfo",
                        "participants": participantsGuess,
                        "round": self.roundNumber,
                        "roundStartTime": ROUND_INFO_DIGEST_TIME_MS + (0 if len(justDiedParticipants)==0 else DIGEST_TIME_MS) + now(),
                        "roundEndTime": ROUND_INFO_DIGEST_TIME_MS + ROUND_TIME_MS + (0 if len(justDiedParticipants)==0 else DIGEST_TIME_MS) + now(),
                        "gameEnded": self.__isEnded(),
                        "aliveCount": self.__getAliveCount(),
                        "target": target,
                        "winners": winners,
                        "justDiedParticipants": justDiedParticipants,
                        "justAppliedRules": list(justAppliedRules),
                        "us": participantsGuess[0],
                        "mode": "solo",
                    }

                    # send gameStart event to app
                    self.qApp.put_nowait(msg)
        except Exception as e:
            print("Exception in soloGame",repr(e))
            self.qApp.put_nowait({
                "event": "gameError",
                "errorMsg": repr(e)
            })
            return

    # purely functional function to find aliveCount from self.gameInfo
    def __getAliveCount(self):
        return len(list(filter(lambda x: not x["isDead"],self.participants)))

    def __isEnded(self): # the game is over when the player is dead
        return self.participants[0]["isDead"] or self.__getAliveCount() <= 1
    
    def __botGuess(self):
        if self.__getAliveCount() == 2:
            r = random.randint(0, 2)
            if r == 2:
                return 100
            else:
                return r
        else:
            upper_limit = (0.8**(self.roundNumber-1)) *100
            return random.randint(0, int(upper_limit))
    
    # mutate p, with new score and whether they are dead
    def __changeScore(self,p,delta):
        p["score"] += delta
        if(p["score"] <= DEAD_LIMIT):
            p["score"] = DEAD_LIMIT; # display -10 instead of -11 or sth
            if(not p["isDead"]):
                p["isDead"] = True;
                return True
        return False
    
    def __del__(self):
        pass