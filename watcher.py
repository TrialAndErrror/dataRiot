import json
import time
from typing import List

from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv()
if not os.environ.get("RIOT_API_KEY"):
    raise PermissionError("No API key found; please provide an API key in the .env file.")

lol_watcher = LolWatcher(os.environ["RIOT_API_KEY"])
my_region = 'na1'
my_name = 'Senor Verde'
me = lol_watcher.summoner.by_name(my_region, my_name)


MATCH_LIST_FILE = Path("data.json")
MATCHES_FOLDER = Path("matches")
MATCH_IDS_FILE = Path("match_ids.json")


def handle_timeout_error(err):
    print('We should retry in {} seconds.'.format(err.headers['Retry-After']))
    print('this retry-after is handled by default by the RiotWatcher library')
    print('future requests wait until the retry-after time passes')


def handle_not_found_error():
    print('Summoner with that ridiculous name not found.')


def handle_api_error(err):
    if err.response.status_code == 429:
        handle_timeout_error(err)
    elif err.response.status_code == 404:
        handle_not_found_error()
    else:
        print(f'API Error found: {err}')


def get_history():
    start_value = 0
    count_per_page = 100

    all_match_ids = {}
    print("Finding Matches...")
    try:
        while True:
            print(f"{start_value} - {start_value + count_per_page - 1}")
            match_id_list = lol_watcher.match.matchlist_by_puuid(region=my_region, puuid=me['puuid'], start=start_value, count=count_per_page)

            if len(match_id_list) == 0:
                print("Found end of match history")
                break

            all_match_ids[str(start_value)] = match_id_list
            time.sleep(1)
            start_value += count_per_page

    except Exception as e:
        print(f'Error found: {e}')
    finally:
        with open(MATCH_LIST_FILE, "w+") as file:
            json.dump(all_match_ids, file, indent=4)


def get_match_info(match_id: str):
    try:
        match_data = lol_watcher.match.by_id(region=my_region, match_id=match_id)
    except ApiError as err:
        handle_api_error(err)
    else:
        with open(MATCHES_FOLDER / f"{match_id}.json", "w+") as file:
            json.dump(match_data, file, indent=4)
    time.sleep(2)


def get_all_match_ids() -> List:
    if not MATCH_IDS_FILE.exists():

        if not MATCH_LIST_FILE.exists():
            print("No match list file found; please run get_history first!")
            return []

        with open(MATCH_LIST_FILE, "r") as file:
            match_list = json.load(file)

        all_match_ids = []
        for list_of_match_ids in match_list.values():
            all_match_ids.extend(list_of_match_ids)

        with open(MATCH_IDS_FILE, "w+") as file:
            json.dump(all_match_ids, file)

    else:
        with open(MATCH_IDS_FILE, "r") as file:
            all_match_ids = json.load(file)

    return all_match_ids


if __name__ == '__main__':
    # get_history()

    all_match_ids = get_all_match_ids()

    MATCHES_FOLDER.mkdir(parents=True, exist_ok=True)

    count = 1
    total = len(all_match_ids)
    for match_id in all_match_ids:
        if not Path(MATCHES_FOLDER / f"{match_id}.json").exists():
            print(f"Fetching Match Data for {match_id} ({count} / {total})")
            get_match_info(match_id)
        else:
            print(f"Found local data for {match_id}")
        count += 1
