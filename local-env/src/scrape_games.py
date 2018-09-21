import os

import firebase_admin
import pandas
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials
from firebase_admin import firestore


def get_pandas_tables(league_id, swid, espn_s2, year, week):
    # Only shows one page worth of result (top 50)
    # 'startIndex' will start lower on list

    url = "http://games.espn.com/ffl/scoreboard"
    r = requests.get(url,
                     params={'leagueId': league_id, 'seasonId': year,
                             'matchupPeriodId': week},
                     cookies={'SWID': swid, 'espn_s2': espn_s2})
    soup = BeautifulSoup(r.content, 'html.parser')
    tables = soup.findAll('table', class_='ptsBased matchup')
    data_frames = []
    for table in tables:
        table_data_frame = pandas.read_html(str(table), flavor='bs4')[0]
        table_data_frame = table_data_frame.iloc[0:2, [0, 1]].reset_index(drop=True)
        table_data_frame.columns = ['raw_name', 'score']
        table_data_frame['name'] = table_data_frame['raw_name'].str.split('(').str[0]
        table_data_frame['owner'] = table_data_frame['raw_name'].str.split(')').str[-1]

        table_data_frame['week'] = week
        table_data_frame['year'] = year
        data_frames.append(table_data_frame)
    return data_frames


def format_game_json(game_data_frames):
    matchups = []
    for game_data_frame in game_data_frames:
        away_team = True
        matchup = {}
        for row in game_data_frame.to_dict(orient='records'):
            team = {
                'owner': row['owner'],
                'name': row['name']
            }
            if away_team:
                matchup.update({'awayTeam': team, 'awayTeamScore': row['score']})
                matchup.update({'week': row['week']})
                away_team = False
            else:
                matchup.update({'homeTeam': team, 'homeTeamScore': row['score']})

        matchups.append(matchup)
    return matchups


def push_games(matchup_data, creds):
    firebase_admin.initialize_app(creds)

    db = firestore.client()
    for matchup in matchup_data:
        matchup_ref = db.collection(u'games').document()
        matchup_ref.set(matchup)


def main():
    firebase_creds = os.environ.get('FIREBASE_CERTIFICATE_FILE')
    league_id = os.environ.get('LEAGUE_ID')
    creds = credentials.Certificate(firebase_creds)
    espn_swid = os.environ.get('ESPN_SWID')
    espn_s2_code = os.environ.get('ESPN_S2_CODE')

    week = 2

    matchup_data_frames = get_pandas_tables(league_id, espn_swid, espn_s2_code, 2018,
                                            week)
    x = format_game_json(matchup_data_frames)

    push_games(creds, x)
