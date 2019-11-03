import requests
import json
import config


# %% fixed parameters
my_api_key = config.BUNGIE_API_KEY  # put your api key here!
baseurl = 'https://bungie.net/Platform/Destiny2/'
baseurl_groupv2 = 'https://bungie.net/Platform/GroupV2/'

#user_platform = 'pc'  # either 'psn' or 'ps4' or 'xbone' or 'xbox'  (pc is busted)
#membership_types = {'xbox': '1', 'xbone': '1', 'psn': '2', 'pc': '3', 'ps4': '2'}

# %% api hooks
def destiny2_api_public(url, api_key):
    """This is the main function for everything. It requests the info from the bungie servers
    by sending a url."""
    my_headers = my_headers = {"X-API-Key": my_api_key}
    response = requests.get(url, headers=my_headers)
    return ResponseSummary(response)


class ResponseSummary:
    """
    Object contains all the important information about the request sent to bungie.
    """

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


def get_members_of_group_url(group_id):
    """Pull all members of a clan. Note clans can only have 100 members max.
        https://bungie-net.github.io/multi/operation_get_GroupV2-GetMembersOfGroup.html"""
    return baseurl_groupv2 + group_id + '/Members/?currentPage=1'


def generate_clan_list(clan_id):
    """Using output of GetMembersOfGroup, create list of member info for clan members:
        each is a dict with username. id, join date. Filters out people not on original
        user's membership type."""
    # Filter out people not on psn
    membership_type = 3

    clan_members_data = []  # dictionary with name: user_name, id: id, and membership_type

    clan_members_url = get_members_of_group_url(clan_id)
    clan_members_summary = destiny2_api_public(clan_members_url, my_api_key)
    # Check out some results
    member_data = clan_members_summary.data['results']  # full data list

    for member in member_data:
        # print(member['destinyUserInfo']['displayName'])  #don't use bungienetuserinfo some don't have

        clan_member = {}
        clan_member['name'] = member['destinyUserInfo']['displayName']
        clan_member['id'] = member['destinyUserInfo']['membershipId']
        clan_member['date_joined'] = member['joinDate']
        clan_members_data.append(clan_member)

    return clan_members_data
