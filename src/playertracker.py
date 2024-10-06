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
  0 : 'Main',
  1 : 'IM',
  2 : 'UIM'
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
  "Dizana's quiver": 0,
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
  return requests.get('https://templeosrs.com/api/groupmembers.php?id={}'.format(group_id)).json()

@sleep_and_retry
@limits(calls=25, period=60)
def get_member_gamemode(member):
  return requests.get('https://templeosrs.com/api/player_info.php?player={}'.format(member)).json()

@sleep_and_retry
@limits(calls=25, period=60)
def get_member_stats(member):
  return requests.get('https://templeosrs.com/api/player_stats.php?player={}'.format(member), params={'bosses': 1}).json()

def get_collectionlog(member):
  return requests.get('https://api.collectionlog.net/collectionlog/user/{}'.format(member)).json()

def get_collectionlog_pets(member):
  return requests.get('https://api.collectionlog.net/items/user/{}'.format(member), params={'pageName': 'All Pets'}).json()

def get_spreadsheet_csv():
  return requests.get('https://docs.google.com/spreadsheets/d/10H-GxmDJ8BAqXVennSXxu5tq7tuZT0tNpJtTxQeMCeA/export?format=csv').text

def parse_spreadsheet_csv(data):
  return list(csv.reader(data.splitlines(), delimiter=','))[1:]

def parse_collectionlog(clog, clog_pets):
  parsed_clog = copy.deepcopy(PARSED_CLOG)
  for k,v in CLOG_PAGES.items():
    tab = v.split("/")[0]
    page = v.split("/")[1]

    if k.split(" ")[-1] == 'KC':
      parsed_clog[k] = clog['collectionLog']['tabs'][tab][page]['killCount'][int(v.split("/")[-1])]['amount']
      continue
    for item in clog['collectionLog']['tabs'][tab][page]['items']:
      if item['name'] == k and item['obtained']:
        parsed_clog[k] = item['quantity']
  parsed_clog['Pets'] = clog_pets['obtainedCount']
  parsed_clog['Total'] = clog['collectionLog']['uniqueObtained']

  return parsed_clog

def check_skill_cape_and_max(stats):
  skill_cape = False
  maxed = False
  if stats['Overall_level'] == 2277:
    maxed = True
  min_level = 99
  for k,v in stats.items():
    if '_level' in k:
      if v < min_level:
        min_level = v
      if v == 99:
        skill_cape = True

  return skill_cape, maxed, min_level

def compute_points(player_tracker):
  points = 0
  for k,v  in CLOG_POINT_CALCULATOR.items():
    if player_tracker['Collection Log'][k] > 0:
      points += v

  if player_tracker['Skill Cape']:
    points += 1
  if player_tracker['Maxed']:
    points += 5
  if player_tracker['Minimum Level'] >= 70:
    points += 1
  if player_tracker['Minimum Level'] >= 80:
    points += 1
  if player_tracker['Minimum Level'] >= 90:
    points += 1
  if player_tracker['Collection Log']['Pets'] == ALL_PETS:
    points += 5

  cox_kc = player_tracker['Collection Log']['CoX KC'] + player_tracker['Collection Log']['CoX CM KC']
  tob_kc = player_tracker['Collection Log']['ToB KC'] + player_tracker['Collection Log']['ToB HM KC']
  toa_kc = player_tracker['Collection Log']['ToA Expert KC']

  if cox_kc >= 10 and tob_kc >= 10 and player_tracker['Collection Log']['ToA KC'] + toa_kc >= 10:
    points +=1
  if cox_kc >= 100 and tob_kc >= 100 and player_tracker['Collection Log']['ToA Expert KC'] >= 100:
    points += 2
  if player_tracker['Collection Log']['CoX CM KC'] >= 100 and player_tracker['Collection Log']['ToB HM KC'] >= 100 and player_tracker['Collection Log']['Cursed phalanx'] > 0:
    points += 4

  raids_kc = cox_kc + tob_kc + toa_kc
  points += math.floor(raids_kc / 250)
  points += math.floor(player_tracker['Total XP'] / 50000000)
  points += math.floor(player_tracker['Collection Log']['Total'] / 100)
  points += math.floor(player_tracker['Collection Log']['Pets'] / 5)
  for k,v in OTHER_POINT_CALCULATOR.items():
    points += v if player_tracker['Other'][k] == True else 0
  return points

def compute_ranks(redis_conn):
  members = [x.lower() for x in get_temple_group_members(LOGIN_TEMPLE_ID)]
  rankings = []
  for member in members:
    p = json.loads(redis_conn.get(member))
    rank = 0
    for _,v in RANKS_EHP_EHB.items():
      if math.floor(p['EHB'] + p['EHP']) >= v:
        rank += 1
        continue
      else:
        break
    for _,v in RANKS_POINTS.items():
      if p['Points'] >= v:
        rank += 1
        continue
      else:
        break
    p['Rank'] = rank
    rankings.append([member, rank, p['Points'], math.floor(p['EHB'] + p['EHP'])])
    redis_conn.set(member, json.dumps(p))

  return rankings

def compute_leaderboard(rankings, redis_conn):
  leaderboard = []
  leaderboard = sorted(rankings, key = lambda x: (x[1], x[2]), reverse=True)

  for i in range(len(leaderboard)):
    p = json.loads(redis_conn.get(leaderboard[i][0]))
    p['Position'] = i+1
    leaderboard[i] = [i+1] + leaderboard[i]
    redis_conn.set(leaderboard[i][0], json.dumps(p))
  return leaderboard

def track_players(redis_conn):

  player_tracker = {}

  for member in [x.lower() for x in get_temple_group_members(LOGIN_TEMPLE_ID)]:
    try:
      gamemode = GAME_MODE[get_member_gamemode(member)['data']['Game mode']]
    except:
      continue
    player_tracker[member] = {
      'Type': gamemode,
      'EHB': 0,
      'EHP': 0,
      'Collection Log': {
        "Champion's cape": 0,
        'CoX CM KC': 0,
        'CoX KC': 0,
        'Cursed phalanx': 0,
        'Fire cape': 0,
        'Infernal cape': 0,
        'Pets': 0,
        'ToA Expert KC': 0,
        'ToA KC': 0,
        'ToB HM KC': 0,
        'ToB KC': 0,
        'Total': 0
      },
      'Minimum Level': 99,
      'Skill Cape' : False,
      'Maxed': False,
      'Other': {
        "Quest cape": False,
        "Music cape": False,
        "Achievement Diary cape": False,
        "Blood Torva": False,
        "Hard CA": False,
        "Elite CA": False,
        "Master CA": False,
        "Grandmaster CA": False
      },
      'Total XP': 0,
      'Points' : 0,
      'Rank': 0,
      'Position': 0
    }

    stats = get_member_stats(member)['data']
    if gamemode == 'Main':
      player_tracker[member]['EHB'] = stats['Ehb']
      player_tracker[member]['EHP'] = stats['Ehp']
    elif gamemode == 'IM' or gamemode == 'HCIM':
      player_tracker[member]['EHB'] = stats['Im_ehb']
      player_tracker[member]['EHP'] = stats['Im_ehp']
    elif gamemode == 'UIM':
      player_tracker[member]['EHB'] = stats['Im_ehb']
      player_tracker[member]['EHP'] = stats['Uim_ehp']
    else:
      print('unknown gamemode!')
      exit(1)

    skill_cape_max_tracker = check_skill_cape_and_max(stats)
    player_tracker[member]['Skill Cape'] = skill_cape_max_tracker[0]
    player_tracker[member]['Maxed'] = skill_cape_max_tracker[1]
    player_tracker[member]['Minimum Level'] = skill_cape_max_tracker[2]
    player_tracker[member]['Total XP'] = stats['Overall']

    clog = get_collectionlog(member)
    clog_pets = get_collectionlog_pets(member)
    try:
      player_tracker[member]['Collection Log'] = parse_collectionlog(clog, clog_pets)
    except:
      pass

  other_data = parse_spreadsheet_csv(get_spreadsheet_csv())
  for member in other_data:
    member_rsn = member[0].lower()
    if member_rsn in player_tracker.keys():
      player_tracker[member_rsn]['Other']['Quest cape'] = True if member[1] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Music cape'] = True if member[2] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Achievement Diary cape'] = True if member[3] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Blood Torva'] = True if member[4] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Hard CA'] = True if member[5] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Elite CA'] = True if member[6] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Master CA'] = True if member[7] == "TRUE" else False
      player_tracker[member_rsn]['Other']['Grandmaster CA'] = True if member[8] == "TRUE" else False
      player_tracker[member_rsn]['Points'] = compute_points(player_tracker[member_rsn])
      redis_conn.set(member_rsn, json.dumps(player_tracker[member_rsn]))