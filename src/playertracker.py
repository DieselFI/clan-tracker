import requests
import copy
import math
import json
import csv
from ratelimit import limits, sleep_and_retry
from pprint import pprint

LOGIN_TEMPLE_ID = 2124
MAX_TOTAL_LEVEL = 2277
MAX_SINGLE_LEVEL = 99
ALL_PETS = 56
GAME_MODE = {
    0 : "Main",
    1 : "IM",
    2 : "UIM",
    3 : "HCIM"
}
CLOG_PAGES = {
    "Champion's cape": "Other/Champion's Challenge",
    "Fire cape": "Bosses/The Fight Caves",
    "Infernal cape": "Bosses/The Inferno",
    "Dizana's quiver (uncharged)": "Bosses/Fortis Colosseum",
    "CoX KC": "Raids/Chambers of Xeric/0",
    "CoX CM KC": "Raids/Chambers of Xeric/1",
    "ToB KC": "Raids/Theatre of Blood/0",
    "ToB HM KC": "Raids/Theatre of Blood/2",
    "ToA KC": "Raids/Tombs of Amascut/0",
    "ToA Expert KC": "Raids/Tombs of Amascut/2",
    "Cursed phalanx": "Raids/Tombs of Amascut"
}
PARSED_CLOG = {
    "Champion's cape": 0,
    "Fire cape": 0,
    "Infernal cape": 0,
    "Dizana's quiver (uncharged)": 0,
    "CoX KC": 0,
    "CoX CM KC": 0,
    "ToB KC": 0,
    "ToB HM KC": 0,
    "ToA KC": 0,
    "ToA Expert KC": 0,
    "Cursed phalanx": 0,
    "Pets": 0,
    "Total": 0
}
CLOG_POINT_CALCULATOR = {
    "Champion's cape": 2,
    "Fire cape": 1,
    "Infernal cape": 5,
    "Dizana's quiver (uncharged)": 3
}
OTHER_POINT_CALCULATOR = {
        "Quest cape": 1,
        "Music cape": 2,
        "Achievement Diary cape": 3,
        "Blood Torva": 3,
        "Hard CA": 1,
        "Elite CA": 2,
        "Master CA": 3,
        "Grandmaster CA": 6
}
RANKS_EHP_EHB = {
    1 : 100,
    2 : 300,
    3 : 600,
    4 : 1200,
    5 : 2000
}
RANKS_POINTS = {
    1 : 5,
    2 : 10,
    3 : 20,
    4 : 40,
    5 : 60
}


@sleep_and_retry
@limits(calls=5, period=300)
def get_temple_group_members(group_id):
    return requests.get("https://templeosrs.com/api/groupmembers.php?id={}".format(group_id)).json()

@sleep_and_retry
@limits(calls=25, period=60)
def get_player_stats(member):
    return requests.get("https://templeosrs.com/api/player_stats.php?player={}".format(member), params={"bosses": 1}).json()

@sleep_and_retry
@limits(calls=25, period=60)
def get_temple_group_member_info(group_id):
    return  requests.get("https://templeosrs.com/api/group_member_info.php?id={}".format(group_id), params={"skills" : 1, "bosses": 1}).json()

def get_collectionlog(member):
    replacements = [' ', '-', '_']
    for char in replacements:
        r = requests.get('https://api.collectionlog.net/collectionlog/user/{}'.format(member.replace(' ', char)))
        if r.status_code == 200:
            return requests.get("https://api.collectionlog.net/collectionlog/user/{}".format(member)).json()

def get_collectionlog_pets(member):
    return requests.get("https://api.collectionlog.net/items/user/{}".format(member), params={"pageName": "All Pets"}).json()

def get_spreadsheet_csv():
    return requests.get("https://docs.google.com/spreadsheets/d/10H-GxmDJ8BAqXVennSXxu5tq7tuZT0tNpJtTxQeMCeA/export?format=csv").text

def parse_spreadsheet_csv(data):
    return list(csv.reader(data.splitlines(), delimiter=","))[1:]

def parse_collectionlog(clog, clog_pets):
    parsed_clog = copy.deepcopy(PARSED_CLOG)
    for k,v in CLOG_PAGES.items():
        tab = v.split("/")[0]
        page = v.split("/")[1]

        if k.split(" ")[-1] == "KC":
            parsed_clog[k] = clog["collectionLog"]["tabs"][tab][page]["killCount"][int(v.split("/")[-1])]["amount"]
            continue
        for item in clog["collectionLog"]["tabs"][tab][page]["items"]:
            if item["name"] == k and item["obtained"]:
                parsed_clog[k] = item["quantity"]
    parsed_clog["Pets"] = clog_pets["obtainedCount"]
    parsed_clog["Total"] = clog["collectionLog"]["uniqueObtained"]

    return parsed_clog

def check_skill_cape_and_max(stats):
    skill_cape = False
    maxed = False
    if stats["Overall_level"] == 2277:
        maxed = True
    min_level = 99
    for k,v in stats.items():
        if "_level" in k:
            if v < min_level:
                min_level = v
            if v == 99:
                skill_cape = True

    return skill_cape, maxed, min_level

def points_verbose_printer(item, points, total_points, verbose=False):
    if verbose:
        print(f"Granted {points} points from {item}. Total: {total_points}")
    return

def compute_points(player_tracker, verbose=False):
    points = 0
    for k,v    in CLOG_POINT_CALCULATOR.items():
        if player_tracker["Collection Log"][k] > 0:
            points += v
            points_verbose_printer(k, v, points, verbose)
        else:
            points_verbose_printer(k, 0, points, verbose)



    if player_tracker["Skill Cape"]:
        points += 1
        points_verbose_printer("Skill Cape", 1, points, verbose)
    if player_tracker["Maxed"]:
        points += 5
        points_verbose_printer("Maxed", 5, points, verbose)
    if player_tracker["Minimum Level"] >= 70:
        points += 1
        points_verbose_printer("Minimum Level 70", 1, points, verbose)
    if player_tracker["Minimum Level"] >= 80:
        points += 1
        points_verbose_printer("Minimum Level 80", 1, points, verbose)
    if player_tracker["Minimum Level"] >= 90:
        points += 1
        points_verbose_printer("Minimum Level 90", 1, points, verbose)
    if player_tracker["Collection Log"]["Pets"] == ALL_PETS:
        points += 5
        points_verbose_printer("All pets", 5, points, verbose)

    cox_kc = player_tracker["Collection Log"]["CoX KC"] + player_tracker["Collection Log"]["CoX CM KC"]
    tob_kc = player_tracker["Collection Log"]["ToB KC"] + player_tracker["Collection Log"]["ToB HM KC"]
    toa_kc = player_tracker["Collection Log"]["ToA Expert KC"]

    if cox_kc >= 10 and tob_kc >= 10 and player_tracker["Collection Log"]["ToA KC"] + toa_kc >= 10:
        points +=1
        points_verbose_printer("10 raids kc", 1, points, verbose)
    else:
        points_verbose_printer("10 raids kc", 0, points, verbose)
    if cox_kc >= 100 and tob_kc >= 100 and player_tracker["Collection Log"]["ToA Expert KC"] >= 100:
        points += 2
        points_verbose_printer("100 raids kc", 2, points, verbose)
    else:
        points_verbose_printer("100 raids kc", 0, points, verbose)
    if player_tracker["Collection Log"]["CoX CM KC"] >= 100 and player_tracker["Collection Log"]["ToB HM KC"] >= 100 and player_tracker["Collection Log"]["Cursed phalanx"] > 0:
        points += 4
        points_verbose_printer("100 challenge raids kc and fang kit", 4, points, verbose)
    else:
        points_verbose_printer("100 challenge raids kc and fang kit", 0, points, verbose)

    raids_kc = cox_kc + tob_kc + toa_kc
    temp_point_counter = 0

    temp_point_counter = math.floor(raids_kc / 250)
    points += temp_point_counter
    points_verbose_printer("raids kc", temp_point_counter, points, verbose)

    temp_point_counter = math.floor(player_tracker["Total XP"] / 50000000)
    points += temp_point_counter
    points_verbose_printer("total xp", temp_point_counter, points, verbose)

    temp_point_counter = math.floor(player_tracker["Collection Log"]["Total"] / 100)
    points += temp_point_counter
    points_verbose_printer("total clog slots", temp_point_counter, points, verbose)

    temp_point_counter = math.floor(player_tracker["Collection Log"]["Pets"] / 5)
    points += temp_point_counter
    points_verbose_printer("total pets", temp_point_counter, points, verbose)

    for k,v in OTHER_POINT_CALCULATOR.items():
        if player_tracker["Other"][k] == True:
            points += v
            points_verbose_printer(k, v, points, verbose)
        else:
            points_verbose_printer(k, 0, points, verbose)
    return points

def update_all_ranks(redis_conn):
    members = [x.lower() for x in get_temple_group_members(LOGIN_TEMPLE_ID)]
    rankings = []
    for member in members:
        p = json.loads(redis_conn.get(member))
        rank = compute_rank(p)
        p["Rank"] = rank
        rankings.append([member, rank, p["Points"], math.floor(p["EHB"] + p["EHP"])])
        redis_conn.set(member, json.dumps(p))
    return rankings

def compute_rank(player_json):
    rank = 0
    for v in RANKS_EHP_EHB.values():
        if math.floor(player_json["EHB"] + player_json["EHP"]) >= v:
            rank += 1
        else:
            break
    for v in RANKS_POINTS.values():
        if player_json["Points"] >= v:
            rank += 1
        else:
            break
    return rank

def compute_leaderboard(rankings, redis_conn):
    leaderboard = []
    leaderboard = sorted(rankings, key = lambda x: (x[1], x[2]), reverse=True)

    for i in range(len(leaderboard)):
        p = json.loads(redis_conn.get(leaderboard[i][0]))
        p["Position"] = i+1
        leaderboard[i] = [i+1] + leaderboard[i]
        redis_conn.set(leaderboard[i][0], json.dumps(p))
    return leaderboard

def track_all_players(verbose=False):
    group_info = get_temple_group_member_info(LOGIN_TEMPLE_ID)

    player_tracker = {}
    for member in group_info["data"]["memberlist"]:
        member_info = group_info["data"]["memberlist"][member]
        gamemode = GAME_MODE[member_info["game_mode"]]
        # Check if GIM
        gim_mode = member_info["gim_mode"]
        if gamemode == "Main" and gim_mode != None and gim_mode != 0:
            gamemode = "GIM"

        player_tracker[member] = {
            "Type": gamemode,
            "EHB": 0,
            "EHP": 0,
            "Collection Log": {
                "Champion's cape": 0,
                "CoX CM KC": 0,
                "CoX KC": 0,
                "Cursed phalanx": 0,
                "Fire cape": 0,
                "Infernal cape": 0,
                "Dizana's quiver (uncharged)": 0,
                "Pets": 0,
                "ToA Expert KC": 0,
                "ToA KC": 0,
                "ToB HM KC": 0,
                "ToB KC": 0,
                "Total": 0
            },
            "Minimum Level": 99,
            "Skill Cape": False,
            "Maxed": False,
            "Other": {
                "Quest cape": False,
                "Music cape": False,
                "Achievement Diary cape": False,
                "Blood Torva": False,
                "Hard CA": False,
                "Elite CA": False,
                "Master CA": False,
                "Grandmaster CA": False
            },
            "Total XP": 0,
            "Points": 0,
            "Rank": 0,
            "Position": 0
        }

        boss_info = member_info["bosses"]
        skill_info = member_info["skills"]
        if gamemode == "Main":
            player_tracker[member]["EHB"] = boss_info["Ehb"]
            player_tracker[member]["EHP"] = skill_info["Ehp"]
        elif gamemode == "IM" or gamemode == "HCIM":
            player_tracker[member]["EHB"] = boss_info["Ehb_im"]
            player_tracker[member]["EHP"] = skill_info["Ehp_im"]
        elif gamemode == "UIM":
            player_tracker[member]["EHB"] = boss_info["Ehb_im"]
            player_tracker[member]["EHP"] = skill_info["Uim_ehp"]
        elif gamemode == "GIM":
            player_tracker[member]["EHB"] = boss_info["Ehb"]
            player_tracker[member]["EHP"] = skill_info["gim_ehp"]
        else:
            print("unknown gamemode!")
            exit(1)

    other_data = parse_spreadsheet_csv(get_spreadsheet_csv())
    for member_data in other_data:
        if member_data[0].lower() in player_tracker.keys():
            player_tracker[member]["Other"]["Quest cape"] = True if member_data[1] == "TRUE" else False
            player_tracker[member]["Other"]["Music cape"] = True if member_data[2] == "TRUE" else False
            player_tracker[member]["Other"]["Achievement Diary cape"] = True if member_data[3] == "TRUE" else False
            player_tracker[member]["Other"]["Blood Torva"] = True if member_data[4] == "TRUE" else False
            player_tracker[member]["Other"]["Hard CA"] = True if member_data[5] == "TRUE" else False
            player_tracker[member]["Other"]["Elite CA"] = True if member_data[6] == "TRUE" else False
            player_tracker[member]["Other"]["Master CA"] = True if member_data[7] == "TRUE" else False
            player_tracker[member]["Other"]["Grandmaster CA"] = True if member_data[8] == "TRUE" else False
            player_tracker[member]["Points"] = compute_points(player_tracker[member], verbose)
            player_tracker[member]["Rank"] = compute_rank(player_tracker[member])
    return player_tracker

def track_player(member: str, verbose=False):

    player_tracker = {}

    if verbose:
        print("Fetching data for {}".format(member))
    stats = get_player_stats(member)["data"]
    gamemode = GAME_MODE[stats["info"]["Game mode"]]
    # Check if GIM
    if gamemode == "Main" and stats["info"]["GIM"] != 0:
        gamemode = "GIM"

    player_tracker[member] = {
        "Type": gamemode,
        "EHB": 0,
        "EHP": 0,
        "Collection Log": {
            "Champion's cape": 0,
            "CoX CM KC": 0,
            "CoX KC": 0,
            "Cursed phalanx": 0,
            "Fire cape": 0,
            "Infernal cape": 0,
            "Dizana's quiver (uncharged)": 0,
            "Pets": 0,
            "ToA Expert KC": 0,
            "ToA KC": 0,
            "ToB HM KC": 0,
            "ToB KC": 0,
            "Total": 0
        },
        "Minimum Level": 99,
        "Skill Cape": False,
        "Maxed": False,
        "Other": {
            "Quest cape": False,
            "Music cape": False,
            "Achievement Diary cape": False,
            "Blood Torva": False,
            "Hard CA": False,
            "Elite CA": False,
            "Master CA": False,
            "Grandmaster CA": False
        },
        "Total XP": 0,
        "Points": 0,
        "Rank": 0,
        "Position": 0
    }

    stats = get_player_stats(member)["data"]
    if gamemode == "Main":
        player_tracker[member]["EHB"] = stats["Ehb"]
        player_tracker[member]["EHP"] = stats["Ehp"]
    elif gamemode == "IM" or gamemode == "HCIM":
        player_tracker[member]["EHB"] = stats["Im_ehb"]
        player_tracker[member]["EHP"] = stats["Im_ehp"]
    elif gamemode == "UIM":
        player_tracker[member]["EHB"] = stats["Im_ehb"]
        player_tracker[member]["EHP"] = stats["Uim_ehp"]
    elif gamemode == "GIM":
        player_tracker[member]["EHB"] = stats["Ehb"]
        player_tracker[member]["EHP"] = stats["Gim_ehp"]
    else:
        print("unknown gamemode!")
        exit(1)

    skill_cape_max_tracker = check_skill_cape_and_max(stats)
    player_tracker[member]["Skill Cape"] = skill_cape_max_tracker[0]
    player_tracker[member]["Maxed"] = skill_cape_max_tracker[1]
    player_tracker[member]["Minimum Level"] = skill_cape_max_tracker[2]
    player_tracker[member]["Total XP"] = stats["Overall"]

    clog = get_collectionlog(member)
    clog_pets = get_collectionlog_pets(member)
    try:
        player_tracker[member]["Collection Log"] = parse_collectionlog(clog, clog_pets)
    except:
        if verbose:
            print("Failed to parse collection data.")
        pass

    other_data = parse_spreadsheet_csv(get_spreadsheet_csv())
    for member_data in other_data:
        if member.lower() == member_data[0].lower():
            player_tracker[member]["Other"]["Quest cape"] = True if member_data[1] == "TRUE" else False
            player_tracker[member]["Other"]["Music cape"] = True if member_data[2] == "TRUE" else False
            player_tracker[member]["Other"]["Achievement Diary cape"] = True if member_data[3] == "TRUE" else False
            player_tracker[member]["Other"]["Blood Torva"] = True if member_data[4] == "TRUE" else False
            player_tracker[member]["Other"]["Hard CA"] = True if member_data[5] == "TRUE" else False
            player_tracker[member]["Other"]["Elite CA"] = True if member_data[6] == "TRUE" else False
            player_tracker[member]["Other"]["Master CA"] = True if member_data[7] == "TRUE" else False
            player_tracker[member]["Other"]["Grandmaster CA"] = True if member_data[8] == "TRUE" else False
            player_tracker[member]["Points"] = compute_points(player_tracker[member], verbose)
            player_tracker[member]["Rank"] = compute_rank(player_tracker[member])
            break
    return player_tracker