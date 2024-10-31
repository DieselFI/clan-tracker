import redis
import argparse
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
    playertracker.track_players(r, args.rsn, args.verbose)
    if args.leaderboard:
        rankings = playertracker.update_all_ranks(r)
        leaderboard = playertracker.compute_leaderboard(rankings, r)
        print(tabulate(leaderboard, headers=['#', 'RSN', 'Rank', 'Points', 'EHB + EHP']))
