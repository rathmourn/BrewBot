# Just a utility script to update bungie-only stats manually

import datetime
import json
import pydest
import os
import config
import asyncio
import time

class ActivityUpdater():
    
    # Clan Activity Updater

    async def clan_activity_update(self):
        print("[*] >>> Updating clan activity scores per background task...")

        for user_file in os.listdir(config.BOT_DB):
            if user_file.endswith(".json"):
                with open(config.BOT_DB + user_file) as user_file_data:
                    user_data = json.load(user_file_data)

                print("[*] >>> BACKGROUND: Updating to {}'s stats...".format(user_data['bungie_name']))

                # Calculate discord stats
#                discord_stats = await activity_manager.get_user_discord_activity_stats(user_data['discord_id'])

                # Update the data in the user's record
                user_data['chat_events'] = 0 # discord_stats['chat_events']
                user_data['characters_typed'] = 0 #discord_stats['characters_typed']
                user_data['vc_minutes'] = 0 # discord_stats['vc_minutes']

                # Calculate bungie stats
                daily_bungie_stats = {}

                today_utc = datetime.datetime.utcnow()
                today_report = today_utc.strftime("%Y-%m-%d")
                reporting_period = (today_utc - datetime.timedelta(days=(int(config.STATISTICS_PERIOD))))

                iter_date = reporting_period

                while iter_date < today_utc:
                    print(">>> STATS FOR: {}".format(iter_date))

                    # See if we have stats already for that date (we don't pull current day))
                    if iter_date.strftime("%Y-%m-%d") in user_data['game_activity'].keys() and iter_date.strftime("%Y-%m-%d") != today_report:
                        daily_bungie_stats.update(
                            {
                                iter_date.strftime("%Y-%m-%d"): user_data['game_activity'][iter_date.strftime("%Y-%m-%d")]
                            }
                        )

                    # If we don't, get them
                    else:
                        bungie_stats = await self.get_user_bungie_activity_stats(user_data['bungie_id'], iter_date)

                        daily_bungie_stats.update(
                            {
                                iter_date.strftime("%Y-%m-%d"): {
                                    "seconds_played": bungie_stats['seconds_played'],
                                    "unique_clan_members_played_with": bungie_stats['unique_clan_members_played_with'],
                                    "clan_members_played_with": bungie_stats['clan_members_played_with']
                                }
                            }
                        )

                    iter_date = iter_date + datetime.timedelta(days=1)

                # Update the data in the user's record.
                user_data['game_activity'] = daily_bungie_stats


                total_seconds_played = 0
                total_unique_members_played_with = 0
                total_clan_members_played_with = 0

                for stat_day, stat_values in user_data['game_activity'].items():
                    total_seconds_played += user_data['game_activity'][stat_day]['seconds_played']
                    total_unique_members_played_with += user_data['game_activity'][stat_day]['unique_clan_members_played_with']
                    total_clan_members_played_with += user_data['game_activity'][stat_day]['clan_members_played_with']

                bonus_multiplier = total_clan_members_played_with + total_unique_members_played_with
                activity_score = total_seconds_played + (user_data['chat_events'] * 60) + \
                                               (user_data['characters_typed'] * 3) * bonus_multiplier

                user_data['clan_activity_score'] = activity_score

                with open(config.BOT_DB + user_file, 'w') as user_file_data:
                    json.dump(user_data, user_file_data)

                print("[*] >>> BACKGROUND: Update to {}'s stats complete.".format(user_data['bungie_name']))

        print("[*] >>> Updating clan activity scores updated in background complete!")


    # End of Clan Roster Updater
    ####################################################################################################################

    async def get_user_bungie_activity_stats(self, bungie_id, day_to_pull):
            stat_results = {}
            today_utc = datetime.datetime.utcnow()
            days_before = config.STATISTICS_PERIOD

            profile_types = [3, 2, 1, 5]
            member_type = None

            for profile_type in profile_types:
                while True:
                    try:
                        destiny = pydest.Pydest(config.BUNGIE_API_KEY)

                        profile_data = await destiny.api.get_profile(profile_type, bungie_id, components=['100'])
                        self.debug_api_call(profile_data)

                        await destiny.close()
                    except:
                       time.sleep(2)
                       await destiny.close()
                       print("Trying call again...")
                       continue 

                    break

                if str(profile_data['ErrorCode']) == "1":

                    member_type = profile_type

                    character_ids = profile_data['Response']['profile']['data']['characterIds']

                    seconds_played = 0
                    clan_members_played_with = 0
                    unique_clan_members_played_with = set()
                    for character_id in character_ids:
                        pull_more_reports = True
                        report_page = 0

                        while pull_more_reports:
                            # Pull the first 25 activities for the characters
                            while True:
                                try:
                                    destiny = pydest.Pydest(config.BUNGIE_API_KEY)

                                    history_report = await destiny.api.get_activity_history(member_type, bungie_id, character_id, count=25, mode=None, page=report_page)
                                    self.debug_api_call(history_report)

                                    await destiny.close()

                                except:
                                   time.sleep(2)
                                   await destiny.close()
                                   print("Trying call again...")
                                   continue 

                                break

                            # See if their profile is set to private
                            if str(history_report['ErrorCode']) == "1665":
                                pull_more_reports = False
                                stat_results.update({"seconds_played": 0})
                                stat_results.update({"clan_members_played_with": 0})
                                stat_results.update({"unique_clan_members_played_with": 0})
                                break

                            # If we don't get a response, we're done
                            if len(history_report['Response']) == 0:
                                pull_more_reports = False
                                break

                            # See if it has any activities in it
                            if 'activities' not in history_report['Response'].keys():
                                break

                            # Increment the page count if we loop back
                            report_page += 1
                            character_activities = history_report['Response']['activities']

                            for character_activity in character_activities:
                                activity_time = datetime.datetime.strptime(character_activity['period'],
                                                                        '%Y-%m-%dT%H:%M:%SZ')

                                # If the activity is within the reporting period; process it
                                if activity_time.date() == day_to_pull.date():
                                    # Calculate seconds played
                                    seconds_played += character_activity['values']['timePlayedSeconds']['basic']['value']
                                    
                                    while True:
                                        try:
                                            destiny = pydest.Pydest(config.BUNGIE_API_KEY)

                                            activity_info = await destiny.api.get_post_game_carnage_report(character_activity['activityDetails']['instanceId'])
                                            self.debug_api_call(activity_info)

                                            await destiny.close()
                                        except:
                                            time.sleep(2)
                                            await destiny.close()
                                            print("Trying call again...")
                                            continue
                                    
                                        break

                                    if len(history_report['Response']) == 0:
                                        pull_more_reports = False
                                        break

                                    # See who they played with in that activity
                                    activity_players = activity_info['Response']['entries']
                                    activity_clan_player_count = 0

                                    for activity_player in activity_players:

                                        # Make sure it isn't the player getting stats pulled on
                                        if str(activity_player['player']['destinyUserInfo']['membershipId']) != str(
                                                bungie_id):

                                            # Deal with fireteam members who may have private profile settings
                                            if str(activity_player['player']['destinyUserInfo']['isPublic']) == "True":
                                                player_name = activity_player['player']['destinyUserInfo']['displayName']
                                            else:
                                                player_name = "<PRIVATE>"

                                            player_id = activity_player['player']['destinyUserInfo']['membershipId']
                                            print("\t\t\tLOOKUP: {} : {}".format(player_name, player_id))
                                            # Find out if the players were in our clans
                                            clan_search_results = self.check_if_clan_member(bungie_id=player_id)

                                            if clan_search_results['is_member']:
                                                activity_clan_player_count += 1
                                                unique_clan_members_played_with.add(player_id)

                                    # Cap at 2.9 to not landslipe PvPers or Iron Banner participants out of control
                                    if activity_clan_player_count > 2:
                                        clan_members_played_with += 2.9
                                    else:
                                        clan_members_played_with += activity_clan_player_count

                                elif activity_time.date() < day_to_pull.date():
                                    pull_more_reports = False
                                    break

                    stat_results.update({"seconds_played": seconds_played})
                    stat_results.update({"clan_members_played_with": clan_members_played_with})
                    stat_results.update({"unique_clan_members_played_with": len(unique_clan_members_played_with)})

                    break
            
                # If we get 1665 (private profile)
                elif str(profile_data['ErrorCode']) == "1665":
                    stat_results.update({"seconds_played": '0'})
                    stat_results.update({"clan_members_played_with": '0'})
                    stat_results.update({"unique_clan_members_played_with": '0'})
                
                # If we get some other error code
                else:
                    stat_results.update({"seconds_played": '0'})
                    stat_results.update({"clan_members_played_with": '0'})
                    stat_results.update({"unique_clan_members_played_with": '0'})

            return stat_results

    def check_if_clan_member(self, bungie_id=None, profile_name=None):
        """Checks the cached roster if member is in the clans.

            Returns (dict):
                            return_results['bungie_id'] = member['id']
                            return_results['bungie_name'] = member['name']
                            return_results['is_member'] = True
        """
        return_results = {}
        return_results['is_member'] = False

        for clan_roster in os.listdir("clans/"):
            with open("clans/" + clan_roster) as clan_data_file:
                clan_data = json.load(clan_data_file)

            for member in clan_data['members']:
                if bungie_id is not None:
                    if str(member['id']) == str(bungie_id):
                        return_results['bungie_id'] = member['id']
                        return_results['bungie_name'] = member['name']
                        return_results['is_member'] = True
                        break

                if profile_name is not None:
                    if str(member['name']).lower() == str(profile_name).lower():
                        return_results['bungie_id'] = member['id']
                        return_results['bungie_name'] = member['name']
                        return_results['is_member'] = True
                        break
            
            # If we've found them, we don't need to keep searching
            if return_results['is_member']:
                break

        return return_results

    def debug_api_call(self, api_response):
        # if api_response['ErrorCode'] != 1:
        time_now = datetime.datetime.utcnow()
        print("{}: ErrorCode: {}, ThrottleSeconds: {}, Message: {}, MessageData: {}".format(time_now,
                                                                                            api_response['ErrorCode'],
                                                                                            api_response[
                                                                                                'ThrottleSeconds'],
                                                                                            api_response['Message'],
                                                                                            api_response[
                                                                                                'MessageData']))
        #if 'Response' in api_response.keys():
            #print("\t\tRESPONSE: {}".format(api_response['Response']))

def main():
    activity_manager = ActivityUpdater()
    
    loop = asyncio.get_event_loop()

    loop.run_until_complete(activity_manager.clan_activity_update())
    loop.close()



if __name__ == '__main__':
    main()
