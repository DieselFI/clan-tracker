import math
import redis
import argparse
import json
from tabulate import tabulate
from src import playertracker


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--rsn", type=str, default=None)
    parser.add_argument("--leaderboard", action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    pool = redis.ConnectionPool(host="localhost", port=6379, db=0)
    r = redis.Redis(connection_pool=pool)

    if args.rsn:
        # Fetch data for specific player
        data = playertracker.track_player(args.rsn)
        r.set(args.rsn, json.dumps(data[args.rsn]))
    else:
        # Fetch data for all clan members
        data = playertracker.track_all_players(args.verbose)
        for k, v in data.items():
            r.set(k, json.dumps(v))
    if args.leaderboard:
        rankings = []
        members = [x.lower() for x in playertracker.get_temple_group_members()]
        for member in members:
            data = json.loads(r.get(member))
            rankings.append([member, data["Rank"], data["Points"], math.floor(data["EHB"] + data["EHP"])])
        leaderboard = playertracker.compute_leaderboard(rankings, r)
        print(tabulate(leaderboard, headers=['#', 'RSN', 'Rank', 'Points', 'EHB + EHP']))
