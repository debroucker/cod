import asyncio
import callofduty
from callofduty import Mode, Platform, Title
import json
import requests
import configparser
import ast
from datetime import datetime
import schedule
import time

associate = {
    1 : Platform.BattleNet,
    2 : Platform.PlayStation,
    3 : Platform.Xbox,
    4 : Platform.Steam,
    5 : Platform.Activision
}

limite = 1
minuteScheduler = 1

def getJsonFromFile(filename) :
    f = open(filename, "r", encoding="utf-8")
    lines = f.read()
    f.close()
    return ast.literal_eval(lines)

def setGoodPlatform(players) : 
    for p in players :
        players[p] = associate[players[p]]
    return players

maps = getJsonFromFile("bd/maps.json")
modes = getJsonFromFile("bd/modes.json")
players = setGoodPlatform(getJsonFromFile("bd/players.json"))

def get_key_map(key, mapp) :
    try :
        return mapp[key]
    except :
        return key

def getUsernamePlayer(players) :
    res = []
    for p in players :
        res.append(p)
    return res

def getKdStr(kd) :
    if float(kd) >= 1 :
        return "pos"
    else :
        return "neg"

def get_rank(level):
    if "Bottom " in level :
        rank = int(level.split('Bottom ')[1].split("%")[0])
        if rank <= 5 : 
            return "Bronze 4"
        elif rank <= 10 : 
            return "Bronze 3"
        elif rank <= 15 : 
            return "Bronze 2"
        elif rank <= 20 : 
            return "Bronze 1"
        elif rank <= 25 : 
            return "Silver 4"
        elif rank <= 30 : 
            return "Silver 3"
        elif rank <= 35 : 
            return "Silver 2"
        elif rank <= 40 : 
            return "Silver 1"
        elif rank <= 45 : 
            return "Gold 4"
        elif rank <= 50 : 
            return "Gold 3"
    if "Top " in level :
        rank = int(level.split('Top ')[1].split("%")[0])
        if rank <= 5 : 
            return "Diamond 1"
        elif rank <= 10 : 
            return "Diamond 2"
        elif rank <= 15 : 
            return "Diamond 3"
        elif rank <= 20 : 
            return "Diamond 4"
        elif rank <= 25 : 
            return "Platinum 1"
        elif rank <= 30 : 
            return "Platinum 2"
        elif rank <= 35 : 
            return "Platinum 3"
        elif rank <= 40 : 
            return "Platinum 4"
        elif rank <= 45 : 
            return "Gold 1"
        elif rank <= 50 : 
            return "Gold 2"


async def main():
    config = configparser.ConfigParser()
    config.read("login.conf")
    login = config.get("CREDENTIALS", "login")
    password = config.get("CREDENTIALS", "pass")
    client = await callofduty.Login(login, password)
    for p in players :
        player = await client.GetPlayer(players[p], p)
        matches = await player.matches(Title.ModernWarfare, Mode.Multiplayer, limit=limite)
        matchesSummary = await player.matchesSummary(Title.ModernWarfare, Mode.Multiplayer, limit=limite)
        kills = int(matchesSummary['all']['kills'])
        deaths = int(matchesSummary['all']['deaths'])
        if deaths == 0 :
            KD = kills
        else :
            KD = round(kills/deaths, 2)
        for match in matches:
            details = await match.details()
            nbPlayersGame = 0
            kdsGame = 0
            levelsGame = 0
            d = {'Date' : str(datetime.now().day) + '/' + str(datetime.now().month) + '/' + str(datetime.now().year), 
            'Map' : get_key_map(details["map"]["mapId"], maps),
            'Mode' : get_key_map(details["mode"], modes),
            'Kills' : kills, 
            'Deaths' : deaths,
            'KD' : KD,
            'Players' : {},
            'LevelTeam1' : {},
            'LevelTeam2' : {},
            'LevelGame' : {}
            }
            teams = await match.teams()
            teamIndex = 0
            for team in teams:
                teamIndex += 1
                nbPlayers = 0
                kds = 0
                levels = 0
                for other_player in team :
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}
                    plat = other_player.platform.value
                    if plat == "battle" :
                        plat += "net"
                    r = requests.get(f'https://cod.tracker.gg/modern-warfare/profile/{plat}/{other_player.username.replace("#", "%23")}/mp', headers=headers)
                    try :
                        kd = r.text.split('<span class="value" data-v-5edf1b22>')[1][0:4]
                        rank = r.text.split('<span class="rank" data-v-5edf1b22>')[1].split("</")[0]
                        if "Bottom" in rank :
                            levels += 50 - int(rank.split('Bottom ')[1].split("%")[0]) + 50
                            levelsGame += 50 - int(rank.split('Bottom ')[1].split("%")[0]) + 50
                        else :
                            levels += int(rank.split('Top ')[1].split("%")[0])
                            levelsGame += int(rank.split('Top ')[1].split("%")[0])
                        nbPlayers += 1
                        nbPlayersGame += 1
                        kds += float(kd)
                        kdsGame += float(kd)
                        d['Players'][other_player.username] = {'kd' : kd, 'kdStr' : getKdStr(kd), 'rank' : get_rank(rank), 'team' : teamIndex}
                    except :
                        None
                if levels//nbPlayers >= 50 :
                    levelStr = f'Bottom {50 - levels//nbPlayers + 50}%'
                else :
                    levelStr = f'Top {levels//nbPlayers}%' 
                kd = round(kds/nbPlayers, 2)
                d['LevelTeam'+str(teamIndex)] = {'kd' : kd, 'kdStr' : getKdStr(kd), 'rank' : get_rank(levelStr)}
            if levelsGame//nbPlayersGame >= 50 :
                levelStr = f'Bottom {50 - levelsGame//nbPlayersGame + 50}%'
            else :
                levelStr = f'Top {levelsGame//nbPlayersGame}%'
            kd = round(kdsGame/nbPlayersGame, 2)
            d['LevelGame'] = {'kd' : kd, 'kdStr' : getKdStr(kd), 'rank' : get_rank(levelStr)}
        try :
            f = open("bd/"+p+"_games.txt", "r", encoding="utf-8")
            line = f.readline()
            f.close()
            dLine = ast.literal_eval(line)
            if (getUsernamePlayer(dLine["Players"]) != getUsernamePlayer(d["Players"]) or dLine["Map"] != d["Map"] or dLine["Mode"] != d["Mode"]) and (d["Kills"] != dLine["Kills"] or d["Deaths"] != dLine["Deaths"]) :
                raise Exception("new game")
        except :
            saveInBdGames(str(d), p)
            saveInBdLevels(get_rank(levelStr).split(" ")[0], kills, deaths, p)
            writeResInHtml(p)
            print(f"NEW GAME | {p} | {d['Map']} - {d['Mode']} | {kills} - {deaths} | {d['LevelGame']['rank']}")

        

def saveInBdGames(res, username) :
    try :
        f = open("bd/"+username+"_games.txt", "r", encoding="utf-8")
        oldRes = f.read()
        f.close()
    except :
        oldRes = ""
    f = open("bd/"+username+"_games.txt", "w", encoding="utf-8")
    f.write(res+"\n"+oldRes)
    f.close()

def saveInBdLevels(rank, kills, deaths, username) :
    res = ""
    lines = []
    try :
        f = open("bd/"+username+"_levels.txt", "r", encoding="utf-8")
        lines = f.readlines()
        for i in range(1, len(lines)) :
            res += lines[i]
        f.close()
        d = ast.literal_eval(lines[0])
        if f'{datetime.now().month}/{datetime.now().year}' != d['Date'] :
            res = lines[0] + res
            raise Exception("not found")
    except :
        d = {'Date' : str(datetime.now().month) + '/' + str(datetime.now().year), 'Bronze' : 0, 'Silver' : 0, 'Gold' : 0, 'Platinum' : 0, 'Diamond' : 0, 'NbGames' : 0, 'Kills' : 0, 'Deaths' : 0, 'KD' : 0, 'KDStr' : 'pos', 'KDEvol' : 'up'}
    d[rank] += 1 
    d["NbGames"] += 1
    d['Kills'] += kills
    d['Deaths'] += deaths
    if d['Deaths'] == 0 :
        d['KD'] = d['Kills']
    else :
        d['KD'] = round(d['Kills'] / d['Deaths'], 2)
    d['KDStr'] = getKdStr(d['KD'])
    if len(lines) != 0 :
        if len(lines) == 1 :
            index = 0
        else :
            index = 1
        dBis = ast.literal_eval(lines[index])
        if d['KD'] >= dBis['KD'] :
            d['KDEvol'] = 'up'
        else : 
             d['KDEvol'] = 'down'
    else :
        d['KDEvol'] = 'up'
    f = open("bd/"+username+"_levels.txt", "w", encoding="utf-8")
    f.write(str(d) + '\n' + res)
    f.close()


def writeResInHtml(username) :
    f = open("res/template.html", "r", encoding="utf-8")
    HtmlLines = f.readlines()
    f.close()
    res = ""
    f = open("bd/"+username+"_levels.txt", "r", encoding="utf-8")
    dictLevelLines = f.readlines()
    f.close()
    f = open("bd/"+username+"_games.txt", "r", encoding="utf-8")
    dictGameLines = f.readlines()
    f.close()
    listStyle = ["table-light", "table-secondary"]
    indexListStyle = 0
    for l in HtmlLines :
        if l.strip() == "TITTLE" :
            res += f"{username}'s Stats"
        #1er page
        elif l.strip() == "RANK":
            level = ast.literal_eval(dictLevelLines[0])
            for key in level :
                if key != 'KDStr' and key != 'KDEvol':
                    res += f"<th>{key}"
                    if key in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'] :
                        res += f" | <div class='circle {key.lower()}'></div>"
                    res += "</th>"
            res += f"<th>KG</th>"
        elif l.strip() == "NBRANK" :
            width = f'{1920}px'
            for line in dictLevelLines:
                level = ast.literal_eval(line)
                res += "<tr>"
                for key in level :
                    if key != 'KDStr' and key != 'KDEvol' :
                        res += f"<th style='width:{width}'>"
                        if key == "KD" :
                            res += f"<div class='kd-{level['KDStr']}'>{level[key]}</div><div class='arrow arrow-{level['KDEvol']}'></div>"
                        elif key in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'] :
                            res += f"{level[key]} | {round(level[key]/level['NbGames']*100,1)}%"
                        else :
                            res += f"{level[key]}"
                        res += "</th>"
                res += f"<th style='width:{width}'>{round(level['Kills']/level['NbGames'],1)}</th>"
                res += "</tr>"
        #2eme page
        elif l.strip() == "GAMELEVEL" :
            res += f"<th>Date</th>"
            res += f"<th>Map</th>"
            res += f"<th>Mode</th>"
            res += f"<th>Kills</th>"
            res += f"<th>Deaths</th>"
            res += f"<th>KD</th>"
            res += f"<th>Team</th>"
            res += f"<th>LevelTeam1</th>"
            res += f"<th>LevelTeam2</th>"
            res += f"<th>LevelGame</th>"
        elif l.strip() == "LEVELDETAIL" :
            for line in dictGameLines :
                game = ast.literal_eval(line)
                res += "<tr>"
                res += f"<th style='width:2000px'>{game['Date']}</th>"
                res += f"<th style='width:3000px'>{game['Map']}</th>"
                res += f"<th style='width:3000px'>{game['Mode']}</th>"
                res += f"<th style='width:1500px'>{game['Kills']}</th>"
                res += f"<th style='width:1500px'>{game['Deaths']}</th>"
                if game['Deaths'] != 0 :
                    res += f"<th style='width:1500px'><div class='kd-{getKdStr(game['Kills'] / game['Deaths'])}'>{game['KD']}</div></th>"
                else :
                    res += f"<th style='width:1500px'><div class='kd-{getKdStr(game['Kills'])}'>{game['KD']}</div></th>"
                keys_view = players.keys()
                keys_iterator = iter(keys_view)
                first_key = next(keys_iterator)
                for p in game['Players'] :
                    if p == first_key:
                        team = game['Players'][p]['team']
                        break
                res += f"<th style='width:1500px'>{team}</th>"
                res += f"<th style='width:3000px'><div class='kd-{game['LevelTeam1']['kdStr']}'>{game['LevelTeam1']['kd']}</div> | {game['LevelTeam1']['rank']} | <div class='circle {game['LevelTeam1']['rank'].split(' ')[0].lower()}'></div></th>"
                res += f"<th style='width:3000px'><div class='kd-{game['LevelTeam2']['kdStr']}'>{game['LevelTeam2']['kd']}</div> | {game['LevelTeam2']['rank']} | <div class='circle {game['LevelTeam2']['rank'].split(' ')[0].lower()}'></div></th>"
                res += f"<th style='width:3000px'><div class='kd-{game['LevelGame']['kdStr']}'>{game['LevelGame']['kd']}</div> | {game['LevelGame']['rank']} | <div class='circle {game['LevelGame']['rank'].split(' ')[0].lower()}'></div></th>"
                res += "</tr>"
        #3eme page
        elif l.strip() == "GAME" :
            game = ast.literal_eval(dictGameLines[0])
            for key in game :
                if key not in ["Kills", "Deaths", "KD", "LevelGame", "LevelTeam1", "LevelTeam2"] :
                    res += f"<th>{key}</th>"
            res += "<th>KD</th>"
            res += "<th>Rank</th>"
        elif l.strip() == "DETAIL" :
            for line in dictGameLines :
                game = ast.literal_eval(line)
                indexListStyle+=1
                for player in game["Players"] :
                    res += f'<tr class="{listStyle[indexListStyle%2]}">'
                    res += f"<th style='width:2000px'>{game['Date']}</th>"
                    res += f"<th style='width:3000px'>{game['Map']}</th>"
                    res += f"<th style='width:3000px'>{game['Mode']}</th>"
                    p = game['Players'][player]
                    res += f"<th style='width:5000px'>{player} ({p['team']}) </th>"
                    res += f"<th style='width:2000px'><div class='kd-{p['kdStr']}'>{p['kd']}</div></th>"
                    res += f"<th style='width:2000px'>{p['rank']} | <div class='circle {p['rank'].split(' ')[0].lower()}'></div></th>"
                    res += "</tr>"
        else :
            res += l
    f = open("res/"+username+"_stat.html", "w", encoding="utf-8")
    f.write(res)
    f.close()


def launchMain() :
    now = datetime.now()
    print(f"{now.strftime('%H:%M')} | scheduler is running...")
    try :
        asyncio.get_event_loop().run_until_complete(main())
    except Exception as e:
        print(f"Error : {str(e)}")


#test
# launchMain()
# asyncio.get_event_loop().run_until_complete(main())
# writeResInHtml('Yves#21759')

#scheduler
launchMain()
schedule.every(minuteScheduler).minutes.do(launchMain)
while True:
    schedule.run_pending()
    time.sleep(1)
