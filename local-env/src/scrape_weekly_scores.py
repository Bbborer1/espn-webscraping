import pandas
import requests
from bs4 import BeautifulSoup

position_map = {'qb': 0, 'rb': 2, 'wr': 6, 'te': 8, 'def': 16, 'k': 17}


def get_page_breaks(players_requested):
    return_list = []
    counter = 0
    while players_requested > 0:
        return_list.append(counter)
        players_requested -= 50
        counter += 50

    return return_list


def get_pandas_table(league_id, swid, espn_s2, year, week, position, start_index):
    # Only shows one page worth of result (top 50)
    # 'startIndex' will start lower on list
    r = requests.get('http://games.espn.com/ffl/leaders',
                     params={'leagueId': league_id, 'seasonId': year,
                             'scoringPeriodId': week,
                             'slotCategoryId': position_map[position],
                             'startIndex': start_index},
                     cookies={'SWID': swid, 'espn_s2': espn_s2})
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('table', class_='playerTableTable')
    table_data_frame = pandas.read_html(str(table), flavor='bs4')[0]
    table_data_frame['week'] = week
    table_data_frame['year'] = year
    table_data_frame['position'] = position

    return table_data_frame


def clean_offensive_stats(data_frame):
    # ['PLAYER, TEAM POS', nan, 'TYPE', 'ACTION', nan, 'OPP',
    #  'STATUS ET', nan, 'C/A', 'YDS', 'TD',
    #  'INT', nan, 'RUSH', 'YDS', 'TD',
    #  nan, 'REC', 'YDS', 'TD', 'TAR',
    #  nan, '2PC', 'FUML', 'TD', nan,
    # 'PTS']

    # remove header rows
    # remove unwanted columns
    table_data_frame = data_frame.iloc[2:49,
                       [0, 2, 5, 6, 8, 9, 10, 11, 13, 14, 15, 17, 18, 19, 20, 22, 23,
                        24,
                        26, 27, 28, 29]].reset_index(drop=True)

    # name the columns
    table_data_frame.columns = ['player', 'owner', 'opponent', 'game_outcome',
                                'passing_complete_per_attempt', 'pass_yards',
                                'pass_tds',
                                'pass_int', 'rush_attempts', 'rush_yards', 'rush_tds',
                                'receptions', 'receiving_yards', 'receiving_tds',
                                'receiving_targets', 'two_point_conversion', 'fumble',
                                'other_tds', 'total_points', 'week', 'year',
                                'position']

    table_data_frame['team'] = table_data_frame['player'].str.split(',').str[1]
    table_data_frame['team'] = table_data_frame['team'].str.replace('\xa0', '_')
    table_data_frame['team'] = table_data_frame['team'].str.split('_').str[
        0].str.strip()

    table_data_frame['player'] = table_data_frame['player'].str.split(',').str[0]
    table_data_frame['passes_completed'] = \
        table_data_frame['passing_complete_per_attempt'].str.split('/').str[0]
    table_data_frame['passes_attempted'] = \
        table_data_frame['passing_complete_per_attempt'].str.split('/').str[1]

    return table_data_frame


def get_full_data_from(league_id, swid, espn_s2, year, week, position,
                       players_requested=50):
    full_data_frame = None

    page_breaks = get_page_breaks(players_requested)
    for page_break in page_breaks:
        data_frame = get_pandas_table(league_id, swid, espn_s2, year, week, position,
                                      page_break)
        if not full_data_frame:
            full_data_frame = data_frame
        else:
            full_data_frame = full_data_frame.append(data_frame)

    return full_data_frame


def get_offensive_stats(full_data_frame):
    table_data_frame = clean_offensive_stats(full_data_frame)

    return table_data_frame.to_dict(orient='records')


def get_kicker_stats():
    pass


def get_def_stats():
    pass


def get_player_data(league_id, swid, espn_s2, year, week, position, players_requested=50):
    offensive_positions = ['qb', 'rb', 'wr', 'te']
    full_date_frames = get_full_data_from(league_id, swid, espn_s2, year, week, position,
                                          players_requested)
    if position in offensive_positions:
        return get_offensive_stats(full_date_frames)
