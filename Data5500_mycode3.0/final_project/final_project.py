import requests
import json
import networkx as nx
from itertools import combinations
import os
import csv
from datetime import datetime

# List of cryptocurrencies to analyze (valid CoinGecko IDs)
cryptocurrencies = ["bitcoin", "ethereum", "binancecoin", "cardano", "solana", "ripple"]

# Initialize a directed graph
g = nx.DiGraph()

# Folder to save currency pair data
data_folder = "data"
os.makedirs(data_folder, exist_ok=True)

# Fetch crypto prices from CoinGecko API
def fetch_prices():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(cryptocurrencies),  # List of crypto IDs separated by commas
        "vs_currencies": "usd"             # Fetch prices in USD
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch prices, status code: {response.status_code}")
        print(f"Error details: {response.text}")
        return {}

# Populate the graph with edges based on fetched prices
def populate_graph(prices):
    edges = []
    for c1, c2 in combinations(cryptocurrencies, 2):  # Pairwise combinations
        rate1 = prices.get(c1, {}).get("usd")
        rate2 = prices.get(c2, {}).get("usd")
        if rate1 and rate2:
            exchange_rate = rate1 / rate2
            edges.append((c1, c2, exchange_rate))
            g.add_edge(c1, c2, weight=exchange_rate)
    print(f"Graph nodes: {g.nodes}")
    print(f"Graph edges: {g.edges(data=True)}")

# Save currency pair data to CSV
def save_to_csv(currency_from, currency_to, exchange_rate):
    filename = f"{data_folder}/currency_pair_{datetime.now().strftime('%Y.%m.%d:%H.%M')}.txt"
    with open(filename, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["currency_from", "currency_to", "exchange_rate"])
        writer.writerow([currency_from, currency_to, exchange_rate])

# Detect cycles out of equilibrium and initiate paper trades
def detect_cycles():
    results = []  # To store path and equilibrium factor
    for n1, n2 in combinations(g.nodes, 2):  # All currency pairs
        for path in nx.all_simple_paths(g, source=n1, target=n2):
            path_weight_to = 1.0
            for i in range(len(path) - 1):
                path_weight_to *= g[path[i]][path[i + 1]]['weight']
            path.reverse()  # Reverse path for equilibrium factor
            path_weight_from = 1.0
            for i in range(len(path) - 1):
                path_weight_from *= g[path[i]][path[i + 1]]['weight']
            factor = path_weight_to * path_weight_from
            results.append((path, path_weight_to, path_weight_from, factor))
            print(f"Equilibrium weight factor: {factor}")
            # Paper trade logic (e.g., log trade request)
            if factor > 1.01 or factor < 0.99:  # Arbitrage threshold
                save_to_csv(path[0], path[-1], factor)
    return results

# Main function
def main():
    prices = fetch_prices()
    if prices:
        populate_graph(prices)
        detect_cycles()

if __name__ == "__main__":
    main()
