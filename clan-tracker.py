import redis
from tabulate import tabulate
from src import playertracker

if __name__ == "__main__":
  pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
  r = redis.Redis(connection_pool=pool)
  playertracker.track_players(r)
  rankings = playertracker.compute_ranks(r)
  leaderboard = playertracker.compute_leaderboard(rankings, r)
  #print(tabulate(leaderboard, headers=['#', 'RSN', 'Rank', 'Points', 'EHB + EHP']))
