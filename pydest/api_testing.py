#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Getting Started using the Destiny 2 Api
An annotated guide to some of the public endpoints available for examining a user's
characters, items, and clan using the Destiny 2 API. You will need to use your api key for
this to work. Just insert it as a string where it says <my_api_key> in the beginning.

It is broken into four parts:
    0: Imports, variables, and fixed parameters defined
    1: Main hooks (destiny2_api_public to make requests, and the url generators)
    2: Helper functions that use those hooks to do useful things
    3: Simple examples of the hooks and helper functions in action. Enter a user_name
        and user_platform to look at their profile, characters, items, clan.
If this were a serious project, these would be different modules.

Code segments are also broken into commented cells (separated by #%%) so you can step through
this cell-by-cell (e.g., in Spyder), sort of like you would in a Jupyter notebook.

Caveats:
1. This code is not optimized, and is verbose. This is intentional. E.g., the
number of calls to 'get_user_id', each of which makes a request to bungie.net, is obscene.
2. Please let me know if you have a suggestion for improvements.
3. Will likely not work for pc players  (they have bnet#s appended to their username
and this code current doesn't handle that).

Acknowledgements:
Thanks to the folks at bungie api discord, the place to go for discussion
and help: https://discord.gg/WJDSUgj
"""
# %% imports
import requests
import json

# %%variables that you might want to change on different runs
user_name = 'rathmourn'  # put name of person whose info/clan you want to explore
user_platform = 'steam'  # either 'psn' or 'ps4' or 'xbone' or 'xbox'  (pc is busted)
save_to_file = 0  # flag: set to 1 if you want certain bits saved to file to peruse

# %% fixed parameters
my_api_key = 'db44f7c876ff4374b68ceb195d7c3cac'  # put your api key here!
baseurl = 'https://bungie.net/Platform/Destiny2/'
baseurl_groupv2 = 'https://bungie.net/Platform/GroupV2/'

membership_types = {'xbox': '1', 'xbone': '1', 'psn': '2', 'steam': '3', 'pc': '4', 'ps4': '2'}

# Following conversions have names I use for user summary stats as keys,
# and names that bungie uses as values for when I extract from end points.
pveKeyConversion = {'numEventsPve': 'activitiesEntered',
                    'kdPve': 'killsDeathsRatio',
                    'durationPlayedPve': 'totalActivityDurationSeconds',
                    'favoriteWeaponPve': 'weaponBestType',
                    'longestKillDistancePve': 'longestKillDistance',
                    'orbsGeneratedPve': 'orbsDropped',
                    'suicideRatePve': 'suicides',
                    'longestKillSpreePve': 'longestKillSpree'}
raidKeyConversion = {'raidAttempts': 'activitiesEntered',
                     'raidClears': 'activitiesCleared'}
pvpKeyConversion = {'numEventsPvp': 'activitiesEntered',
                    'numWinsPvp': 'activitiesWon',
                    'winLossRatioPvp': 'winLossRatio',
                    'kdPvp': 'killsDeathsRatio',
                    'durationPlayedPvp': 'totalActivityDurationSeconds',
                    'favoriteWeaponPvp': 'weaponBestType',
                    'mostKillsPvp': 'bestSingleGameKills',
                    'longestKillSpreePvp': 'longestKillSpree',
                    'suicideRatePvp': 'suicides'}


# %% api hooks
def destiny2_api_public(url, api_key):
    """This is the main function for everything. It requests the info from the bungie servers
    by sending a url."""
    my_headers = my_headers = {"X-API-Key": my_api_key}
    response = requests.get(url, headers=my_headers)
    return ResponseSummary(response)


class ResponseSummary:
    '''
    Object contains all the important information about the request sent to bungie.
    '''

    def __init__(self, response):
        self.status = response.status_code
        self.url = response.url
        self.data = None
        self.message = None
        self.error_code = None
        self.error_status = None
        self.exception = None
        if self.status == 200:
            result = response.json()
            self.message = result['Message']
            self.error_code = result['ErrorCode']
            self.error_status = result['ErrorStatus']
            if self.error_code == 1:
                try:
                    self.data = result['Response']
                except Exception as ex:
                    print("ResponseSummary: 200 status and error_code 1, but there was no result['Response']")
                    print("Exception: {0}.\nType: {1}".format(ex, ex.__class__.__name__))
                    self.exception = ex.__class__.__name__
            else:
                print('No data returned for url: {0}.\n {1} was the error code with status 200.'.format(self.url,
                                                                                                        self.error_code))
        else:
            print('Request failed for url: {0}.\n.Status: {0}'.format(self.url, self.status))

    def __repr__(self):
        """What will be displayed/printed for the class instance."""
        disp_header = "<" + self.__class__.__name__ + " instance>\n"
        disp_data = ".data: " + str(self.data) + "\n\n"
        disp_url = ".url: " + str(self.url) + "\n"
        disp_message = ".message: " + str(self.message) + "\n"
        disp_status = ".status: " + str(self.status) + "\n"
        disp_error_code = ".error_code: " + str(self.error_code) + "\n"
        disp_error_status = ".error_status: " + str(self.error_status) + "\n"
        disp_exception = ".exception: " + str(self.exception)
        return disp_header + disp_data + disp_url + disp_message + \
               disp_status + disp_error_code + disp_error_status + disp_exception


"""
URL GENERATORS
The following functions create urls in the format that the bungie servers want them.
In the docs for each function I give the url to bungie docs, partly to help but also so
you can see what I may have left out --- I'm not always including all possible query strings.
I named each url generator according to the bungie end point (e.g., if the end point is X
then the function is X_url)
"""


def search_destiny_player_url(user_name, user_platform):
    """Main point is to get the user's id from their username.
        https://bungie-net.github.io/multi/operation_get_Destiny2-SearchDestinyPlayer.html
    """
    membership_type = membership_types[user_platform]
    return baseurl + 'SearchDestinyPlayer/' + membership_type + '/' + user_name + '/'


def get_profile_url(user_name, user_platform, components, my_api_key):
    """Get information about different aspects of user's character like equipped items.
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetProfile.html
    Note components are just strings: '200,300' : you need at least one component."""
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    return baseurl + membership_type + '/' + 'Profile/' + user_id + '/?components=' + components


def get_character_url(user_name, user_platform, character_id, components, my_api_key):
    """Similar to get_profile but does it for a single character. Note individual character
    id's are returned by get_profile.
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetCharacter.html """
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    return baseurl + membership_type + '/' + 'Profile/' + user_id + \
           '/Character/' + character_id + '/?components=' + components


def get_item_url(user_name, user_platform, item_instance_id, components, my_api_key):
    """Pull item with item instance id (for instance if you have two instances of
    Uriel's Gift, this will let you pull information about one particular instance.
    You will get the itemInstanceId from item stats returned from get_profile or
    get_character.
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetItem.html"""
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    return baseurl + membership_type + '/Profile/' + user_id + \
           '/item/' + item_instance_id + '/?components=' + components


def get_entity_definition_url(entity_hash, entity_type, my_api_key):
    """
    Hooking up with the manifest!
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetDestinyEntityDefinition.html
    If you've got a hash, and know the entity type, you can use this (or just download
    the manifest and make your  own database to do it 10x faster)
    """
    return baseurl + 'Manifest/' + entity_type + '/' + entity_hash


def get_groups_for_member_url(user_name, user_platform, my_api_key):
    """This is how I find the groupId for the clan a user is in. You need the group
    id to do more interesting things like pull all members of a clan (see get_group_members)
        https://bungie-net.github.io/multi/operation_get_GroupV2-GetGroupsForMember.html"""
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    return baseurl_groupv2 + 'User/' + membership_type + '/' + user_id + '/0/1/'  # 0/1 are filter/groupType


def get_members_of_group_url(group_id):
    """Pull all members of a clan. Note clans can only have 100 members max.
        https://bungie-net.github.io/multi/operation_get_GroupV2-GetMembersOfGroup.html"""
    return baseurl_groupv2 + group_id + '/Members/?currentPage=1'


def get_activity_history_url(user_name, user_platform, character_id, \
                             activity_mode='None', page='0', count='100'):
    """Returns useful history of activities, filtered by tyupe if you want (e.g.,
    pvp, pve, etc: see modes below)
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetActivityHistory.html
    Queries:
        count: total number of results to return:
        mode: filter for activity mode to return (None returns all activities--see below)
        page: page number of results to return, starting with 0.
    Sample of modes (this is not all of them)
      all: None; story:  2; strike: 3; raid: 4; PvP: 5; Patrol 6; PvE 7; Clash  12
      Nightfall 16; Trials: 39; Social: 40 (returns nada)
    """
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    query_string = '?mode=' + activity_mode + '&page=' + page + '&count=' + count
    return baseurl + membership_type + '/Account/' + user_id + '/Character/' + \
           character_id + '/Stats/Activities/' + query_string


def get_historical_stats_url(user_name, user_platform, character_id, my_api_key, activity_modes='None'):
    """Return tons of useful stats about a character (or set character_id = '0' for
    all character data lumped together).
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetHistoricalStats.html
    Note modes are from the same list as above with GetActivityHistory."""
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    query_string = '?modes=' + activity_modes
    return baseurl + membership_type + '/Account/' + user_id + '/Character/' + \
           character_id + '/Stats/' + query_string


def get_historical_stats_for_account_url(user_name, user_platform, my_api_key):
    """Get lots of stats almost as useful as get historical stats for character, but not quite as
    no raid data.
        https://bungie-net.github.io/multi/operation_get_Destiny2-GetHistoricalStatsForAccount.html"""
    user_id = get_user_id(user_name, user_platform, my_api_key)
    membership_type = membership_types[user_platform]
    return baseurl + membership_type + '/Account/' + user_id + '/Stats/'


# %% helper functions
"""
HELPER FUNCTIONS (ImHelping)
These functions all use the above url-generators and api endpoints, or some processed
data from the endpoints, in the use-case bits below.
"""


def get_user_id(user_name, user_platform, my_api_key):
    """Uses search_destiny_player end point to get user id. Returns None if there is a problem."""
    player_summary = destiny2_api_public(search_destiny_player_url(user_name, user_platform), my_api_key)
    if player_summary.error_code == 1:
        if player_summary.data:
            return player_summary.data[0]['membershipId']
        else:
            print('There is no data for {0} on {1}'.format(user_name, user_platform))
            return None
    else:
        print('There was an error getting id for {0}. Status: {1}'.format(user_name, player_summary.status))
        return None


def extract_item_stats(item_hash, my_api_key):
    """
    For item_hash, return dict containing its stats by name and value (and the name of the
    item with its type).  Note some items have no stats, but for weapons and armor you
    will get the standards you see in game.
    """
    item_url = get_entity_definition_url(item_hash, 'DestinyInventoryItemDefinition', my_api_key)
    item_summary = destiny2_api_public(item_url, my_api_key)
    stat_names_values = {}
    item_name = item_summary.data['displayProperties']['name']
    item_type = item_summary.data['itemTypeAndTierDisplayName']
    item_stats = item_summary.data['stats']['stats']
    stat_names_values['name'] = item_name
    stat_names_values['type'] = item_type
    print('Extracting stats for {0}'.format(item_name))
    for statHash in item_stats:
        tmp_url = get_entity_definition_url(statHash, 'DestinyStatDefinition', my_api_key)
        tmp_summary = destiny2_api_public(tmp_url, my_api_key)
        try:
            stat_name = tmp_summary.data['displayProperties']['name']
            stat_value = item_stats[statHash]['value']
            stat_names_values[stat_name] = stat_value
            print('Extracted {0} stats...'.format(stat_name))
        except KeyError:  # this is common some hashes are undefined
            print('Warning: KeyError for statHash {0}'.format(statHash))
            continue
    print("Finished collecting stats for {0}\n".format(item_name))
    return stat_names_values


def summarize_pve(user_name, user_stats):
    """pull stats of interest from accounts pve history. Uses the user_stats
    dictionary created by GetHistoricalStats"""
    user_pve_summary = {}
    allPvE = user_stats['allPvE']
    if allPvE:
        pve_stats = allPvE['allTime']
        for newKey, oldKey in pveKeyConversion.items():
            if newKey == 'suicideRatePve':
                user_pve_summary[newKey] = pve_stats[oldKey]['pga']['displayValue']
            else:
                user_pve_summary[newKey] = pve_stats[oldKey]['basic']['displayValue']
    else:
        user_pve_summary['numEventsPve'] = None
    # Raid stats are stored separately
    raid_dat = user_stats['raid']
    if raid_dat:
        raid_stats = raid_dat['allTime']
        for newKey, oldKey in raidKeyConversion.items():
            user_pve_summary[newKey] = raid_stats[oldKey]['basic']['displayValue']
    else:
        user_pve_summary['raidAttempts'] = None
    user_pve_summary['userName'] = user_name
    return user_pve_summary


def summarize_pvp(user_name, user_stats):
    """pull stats of interest from accounts' pvp history. Uses user_stats structure returned
    by GetHistoricalStats."""
    user_pvp_summary = {}
    allPvP = user_stats['allPvP']
    if allPvP:  # if they have done any pvp
        pvp_stats = allPvP['allTime']
        for newKey, oldKey in pvpKeyConversion.items():
            if newKey == 'suicideRatePvp':
                user_pvp_summary[newKey] = pvp_stats[oldKey]['pga']['displayValue']
            else:
                user_pvp_summary[newKey] = pvp_stats[oldKey]['basic']['displayValue']
    else:  # they have not done any pvp
        user_pvp_summary['numEventsPvp'] = None
    user_pvp_summary['userName'] = user_name
    return user_pvp_summary


def summarize_player_performance(user_name, user_stats):
    """Pools pvp and pve performance stats into one dictionary. Calls
    summarize_pve and summarize_pvp"""
    pve_stats = summarize_pve(user_name, user_stats)
    pvp_stats = summarize_pvp(user_name, user_stats)
    # merging dicts: http://treyhunner.com/2016/02/how-to-merge-dictionaries-in-python/
    return {**pve_stats, **pvp_stats}


def generate_clan_list(member_data, clan_platform):
    """Using output of GetMembersOfGroup, create list of member info for clan members:
        each is a dict with username. id, join date. Filters out people not on original
        user's membership type."""
    # Filter out people not on psn
    membership_type = membership_types[clan_platform]
    clan_members_data = []  # dictionary with name: user_name, id: id, and membership_type
    for member in member_data:
        # print(member['destinyUserInfo']['displayName'])  #don't use bungienetuserinfo some don't have
        clan_member = {}
        clan_member['membership_type'] = str(member['destinyUserInfo']['membershipType'])
        if clan_member['membership_type'] == membership_type:
            # print('go')
            clan_member['name'] = member['destinyUserInfo']['displayName']
            clan_member['id'] = member['destinyUserInfo']['membershipId']
            clan_member['date_joined'] = member['joinDate']
            clan_members_data.append(clan_member)
    return clan_members_data


def print_clan_roster(clan_members_data):
    """Print name, membership type, id, and date joined. Just a way to organize columns."""
    name_list = [clanfolk['name'] for clanfolk in clan_members_data]
    col_width = max(len(word) for word in name_list)
    for clan_member in clan_members_data:
        memb_name = clan_member['name']
        length_name = len(memb_name)
        num_spaces = col_width - length_name
        memb_name_extended = memb_name + " " * num_spaces
        print("{0}\tMembership type: {1}\t Id: {2}\tJoined: {3}".format(memb_name_extended, \
                                                                        clan_member['membership_type'],
                                                                        clan_member['id'], clan_member['date_joined']))


def summarize_clan_performance(clan_members_data, clan_platform, my_api_key):
    """Run summarize_player_performance for each player in clan_members_data dictionary.
    """
    num_members = len(clan_members_data)
    clan_performance = {}
    debug_bits = []
    player_count = 1
    print('\n *\n About to get stats for {0} members of clan\n *'.format(num_members))
    for clan_member in clan_members_data:
        member_name = clan_member['name']
        print('Processing player {0} (name/id): ({1}/{2})'.format(player_count, \
                                                                  member_name, clan_member['id']))
        try:
            member_stats_url = get_historical_stats_url(member_name, clan_platform, \
                                                        '0', my_api_key, activity_modes='4,5,7')
            member_response = destiny2_api_public(member_stats_url, my_api_key)
            member_performance = summarize_player_performance(member_name, member_response.data)
            member_performance['dateJoined'] = clan_member['date_joined']
            clan_performance[member_name] = member_performance
        except Exception as ex:
            print('failed with {0}. Exception: {1}'.format(member_name, ex.__class__.__name__))
            debug_bits.append({'member': member_name, 'exception': ex.__class__.__name__})
        player_count += 1
        # if player_count == 20:  #for debugging
        #    break
    return clan_performance, debug_bits


def print_clan_performance(clan_performance):
    """Print tiny bit of selected info about each member in clan. This is a test, it really
    is just a sliver of the information available in clan_performance."""
    for member in clan_performance:
        print(member)
        member_data = clan_performance[member]
        user_summary = "{0} joined on {1}.\n".format(member_data['userName'], member_data['dateJoined'])

        if member_data['numEventsPve']:
            pve_summary = "PvE: Played {0} matches in {1} with {2} orbs generated total.\n". \
                format(member_data['numEventsPve'], member_data['durationPlayedPve'], \
                       member_data['orbsGeneratedPve'])
        else:
            pve_summary = "PvE: They have played no PvE yet.\n"

        if member_data['raidAttempts']:
            raid_summary = "They have attempted the raid {0} times with {1} clears.\n". \
                format(member_data['raidAttempts'], member_data['raidClears'])
        else:
            raid_summary = "They have not yet attempted the raid.\n"

        if member_data['numEventsPvp']:
            pvp_summary = "PvP: {0} matches in {1} with a {2} kd and {3} w/l.\n". \
                format(member_data['numEventsPvp'], member_data['durationPlayedPvp'], \
                       member_data['kdPvp'], member_data['winLossRatioPvp'])
        else:
            pvp_summary = "PvP: They have played no PvP yet.\n"

        print(user_summary + pve_summary + raid_summary + pvp_summary)


def print_misadventure_rates(clan_performance):
    """Prints misadventure rates for each member...Not pretty yet or anything just an
    example of something you can do."""
    for member in clan_performance:
        member_data = clan_performance[member]
        if member_data['numEventsPve']:
            pve_printout = "{0} misadventure rate pve {1}. ".format(member_data['userName'],
                                                                    member_data['suicideRatePve'])
        else:
            pve_printout = "{0}: No pve.".format(member_data['userName'])
        if member_data['numEventsPvp']:
            pvp_printout = "misadventure rate pvp: {0}".format(member_data['suicideRatePvp'])
        else:
            pvp_printout = " No pvp."
        print(pve_printout + pvp_printout)


def save_readable_json(data, filename):
    """This is if you want to save response data to filename in human-readable json format"""
    with open(filename, 'w') as fileObject:
        try:
            fileObject.write(json.dumps(data, indent=3))
            print('Saved data to ' + filename)
        except:
            print('ya blew it saving ' + filename)


# %% ########################################################
#        END FUNCTION AND CLASS DEFINITIONS             #
#########################################################


"""
EXAMPLES
"""
if __name__ == '__main__':
    # %%SearchDestinyPlayer to get user id
    player_url = search_destiny_player_url(user_name, user_platform)
    player_summary = destiny2_api_public(player_url, my_api_key)
    user_id = player_summary.data[0]['membershipId']

    # %% Or just get id using a helper function
    user_id_alt = get_user_id(user_name, user_platform, my_api_key)

    # %%GetProfile
    # Component types include: 100 profiles; 200 characters; 201 non-equipped items (need oauth);
    # 205: CharacterEquipment: what they currently have equipped. All can see this
    components = '200,205'
    profile_url = get_profile_url(user_name, user_platform, components, my_api_key)
    user_profile_summary = destiny2_api_public(profile_url, my_api_key)

    # %%extract character id's from profile
    user_characters = user_profile_summary.data['characters']['data']
    character_ids = list(user_characters.keys())
    user_character_0 = user_characters[character_ids[0]]

    # %%GetCharacter
    # This basically is GetProfile but for just one character that you show an id for
    # Note if you search for inventory components (201) if you get nothing it might say privacy: 2
    # public:1, private: 2
    character_components = '201,205'
    char_url = get_character_url(user_name, user_platform, character_ids[0], character_components, my_api_key)
    character_summary = destiny2_api_public(char_url, my_api_key)

    # Note this contains equipment and itemComponents (later isempty)
    character_items = character_summary.data['equipment']['data']['items']  #
    first_item = character_items[0]
    item_instance_id = first_item['itemInstanceId']
    item_hash = str(first_item['itemHash'])  # wtf is this? you might ask

    second_item = character_items[1]
    second_item_hash = str(second_item['itemHash'])

    fifth_item = character_items[4]
    fifth_item_hash = str(fifth_item['itemHash'])

    """
    Characteritems includes all equipped stuff. But you can't just read them off the data.
    They are encoded in hashes. To decode them you need to use the manifest. Which brings
    us to...GetEntityDefinition: https://destiny.plumbing/
    """

    # %% Access manifest via GetDestinyEntityDefinition,
    item_url = get_entity_definition_url(item_hash, 'DestinyInventoryItemDefinition', my_api_key)
    item_summary = destiny2_api_public(item_url, my_api_key)

    # now you have all sorts of information about that inventory item:
    # This will pretty much have everything you need
    item_data = item_summary.data

    print(item_data.keys())
    # Let's get name and type
    item_data['displayProperties']
    item_name = item_data['displayProperties']['name']
    item_type = item_data['itemTypeAndTierDisplayName']
    print("\nWhat you've got here is a {0}. It's name is {1}.".format(item_type, item_name))

    # %% If you want to pull some stats, you will also need to access statHash
    item_stats = item_data['stats']['stats']
    # EXplore first stat
    entity_type = 'DestinyStatDefinition'
    first_stat = list(item_stats.keys())[0]
    stat_value = item_stats[first_stat]['value']
    stat_url = get_entity_definition_url(first_stat, entity_type, my_api_key)
    stat_summary = destiny2_api_public(stat_url, my_api_key)
    stat_summary_data = stat_summary.data['displayProperties']
    stat_name = stat_summary_data['name']
    stat_description = stat_summary_data['description']

    print("The first stat is {0} and its value is {1}".format(stat_name, stat_value))

    # %% Because that's so tedious, I made a helper function:
    # EXTRACT_ITEM_STATS that prints out all stats for an item
    first_item_stats = extract_item_stats(item_hash, my_api_key)
    fifth_item_stats = extract_item_stats(fifth_item_hash, my_api_key)

    # print results (would be nice to have a better function for this)
    print("\n" + str(first_item_stats) + "\n")
    print("\n" + str(fifth_item_stats) + "\n")

    """
    You will notice extracting stats by url queries is slow it takes many seconds to run.
    So you should download the manifest so you don't have to futz around with
    request.get and such any more!
    For more on how to do this see:
        https://github.com/vpzed/Destiny2-API-Info/wiki/Manifest-Introduction
        http://allynh.com/blog/creating-a-python-app-for-destiny-part-5-reading-a-characters-inventory-and-vault-contents/
    """

    # %%GetItem testing
    item_components = '302,304,307'
    item_url = get_item_url(user_name, user_platform, item_instance_id, item_components, my_api_key)
    item_instance = destiny2_api_public(item_url, my_api_key)

    # %% GET_ACTIVITY_HISTORY
    ###testing full default
    all_activity_url = get_activity_history_url(user_name, user_platform, character_ids[0])
    all_activity_summary = destiny2_api_public(all_activity_url, my_api_key)
    all_activities = all_activity_summary.data['activities']  # this is a list

    # look at a couple if you want
    first_all = all_activities[0]
    last_all = all_activities[-1]

    # %% GET_HISTORICAL_STATS_FOR_ACCOUNT (nb: this is not as good as character-based)
    # use the char-based one which is next it has raid information
    user_history_url = get_historical_stats_for_account_url(user_name, user_platform, my_api_key)
    user_history = destiny2_api_public(user_history_url, my_api_key)
    if save_to_file:
        save_readable_json(user_history.data, 'user_stats.txt')

    # %% GET_HISTORICAL_STATS_CHAR (for character: this seems more informative
    # than the previous, as you can get raid info. Set char_id = '0' to pull account
    # totals for all characters
    main_stats_url = get_historical_stats_url(user_name, user_platform, '0', \
                                              my_api_key, activity_modes='4,5,7')
    main_stats = destiny2_api_public(main_stats_url, my_api_key)

    # Example of how you might pull some data
    pve_dat = main_stats.data['allPvE']['allTime']
    if main_stats.data['raid']:  # has user attempted rate
        raid_dat = main_stats.data['raid']['allTime']
        raid_clears = raid_dat['activitiesCleared']['basic']['displayValue']
    else:
        raid_dat = None
    if main_stats.data['allPvP']:  # has user done pvp
        pvp_dat = main_stats.data['allPvP']['allTime']
    else:
        pvp_dat = None

    #########################
    # %%TEST HELPER FUNCTIONS:
    # SUMMARIZE_PVP, SUMMARIZE_PVE, AND SUMMARIZE_PLAYER_PERFORMANCE
    user_stats = main_stats.data
    user_pvp = summarize_pvp(user_name, user_stats)
    user_pve = summarize_pve(user_name, user_stats)
    user_summary_stats = summarize_player_performance(user_name, user_stats)

    ##################
    # %% CLAN STUFF
    ##################
    # TEST GET_GROUPS_FOR_MEMBER
    get_groups_url = get_groups_for_member_url(user_name, user_platform, my_api_key)
    groups_summary = destiny2_api_public(get_groups_url, my_api_key)

    # %% set flag for whether user is in clan or not
    if groups_summary.data['results']:
        user_in_clan = 1
    else:
        user_in_clan = 0
        print("User {0} is not in a clan. Why are you all alone, {0}?".format(user_name))

    # %%#Summarize basic info about the clan they are in
    if user_in_clan:
        user_clan_data = groups_summary.data['results'][0]['group']
        clan_id = user_clan_data['groupId']
        clan_name = user_clan_data['name']
        clan_description = user_clan_data['about']
        clan_motto = user_clan_data['motto']
        clan_num_members = user_clan_data['memberCount']
        print("\n\nUser is in the clan named '{0}'. Their motto is '{1}'.\nThere are currently {2} members.\n\n" \
              "Their book-lenth description is...\n{3}".format(clan_name, clan_motto, clan_num_members,
                                                               clan_description))

        # %% TEST GET_MEMBERS_FOR_GROUP (get all clan members)
        clan_members_url = get_members_of_group_url(clan_id)
        clan_members_summary = destiny2_api_public(clan_members_url, my_api_key)
        # Check out some results
        num_members = clan_members_summary.data['totalResults']
        member_data = clan_members_summary.data['results']  # full data list
        clan_members_data = generate_clan_list(member_data, user_platform)

        # %% Display clan roster in a pretty way
        print_clan_roster(clan_members_data)

        # %% TEST SUMMARIZE_CLAN_PERFORMANCE
        clan_performance, debug_performance = \
            summarize_clan_performance(clan_members_data, user_platform, my_api_key)
        if save_to_file:
            save_readable_json(clan_performance, 'clan_stats.txt')

        # Helper functions to print some stuff for fun
        print_clan_performance(clan_performance)
        print_misadventure_rates(clan_performance)

    """Good luck, guardian. I'm sorry I didn't have time to explain what I didn't have
    time to understand. Time to go drink some vex milk."""
