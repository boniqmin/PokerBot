import pickle
import cards_backend

# TODO: the commented section below is currently copy-pasted into game_runner, due to pickle not recognizing objects
# TODO: from other files. should be fixable by importing the object explicitly (i.e. Gamestate, not saver.Gamestate)
# class GameState:
#     def __init__(self, channel, host, players):
#         self.id = channel.id
#         # self.playing = False
#         # self.joining = False    # TODO remove?
#         self.players = players #[Player(p,0) for p in players]  # Player attributes may be changed, but not this list
#         self.buyin = 1000
#         self.host_id = host.id
#         self.roundstate = None
#         self.sm_blind_index = 0
#         self.save()
#
#
#     def save(self): #issue: can't pickle channel object, fixed?
#         save_file = open("./files/savefile.dat", 'rb')
#         save_dict = pickle.load(save_file)
#         save_file.close()
#
#         save_dict[self.id] = self
#         save_file = open("./files/savefile.dat", 'wb')
#         pickle.dump(save_dict, save_file)
#         save_file.close()
#
#     @property
#     def n_current_players(self):
#         return len(self.current_players)
#
#     @property
#     def current_players(self):
#         return [p for p in self.players if not p.eliminated]
#
#     # def new_round(self):
#     #     self.roundstate = RoundState()
#
#     # bedenk welke nuttig is ^ \/
#     def end_round(self):
#         self.roundstate = None
#         for p in self.players:
#             p.prstate = None
#
#
#
#
#
#
# def get_gamestate(channel):
#     save_file = open("./files/savefile.dat", 'rb')
#     save_dict = pickle.load(save_file)
#     save_file.close()
#     if channel.id in save_dict:
#         return save_dict[channel.id]
#     else:
#         raise KeyError("This channel has no running games")


# def channel_occupied(channel):
#     pass


class RoundState: # TODO: make some of these private/local to init. Will poker() pass sm_blind player or index?
    def __init__(self, current_players, sm_blind_index, community_cards):
        self.min_bet = 0
        self.min_raise = 0
        self.current_players = current_players
        self.previous_raiser = None
        self.sm_blind_index = sm_blind_index    # this one is not changed
        self.player_index = sm_blind_index      # this one keeps track of whose turn it is
        self.turn_number = 1
        self.cycle_number = 0
        self.new_cycle_flag = False
        self.community_cards = cards_backend.CardSet(community_cards)
        self.public_cards = cards_backend.CardSet(5*[cards_backend.Card(0,0)])
        self.sidepots = [] #[0]

    def next_player(self):  # sets turn player to next one
        for i in range(len(self.current_players)):  # prevent infinite loops
            print('Next_player loop')
            self.player_index = (self.player_index + 1) % len(self.current_players)

            if self.turn_player == self.previous_raiser:  # edit
                print('new cycle')
                self.new_cycle_flag = True
                # self.cycle_number += 1

            print("    ", self.turn_player.name)
            print("        folded:", self.turn_player.prstate.folded)
            print("        all-in:", self.turn_player.prstate.all_in)

            if not self.turn_player.eliminated and not self.turn_player.prstate.folded and \
                    not self.turn_player.prstate.all_in:
                self.turn_number += 1
                return
        print("You dun gooft (next_player in saver.RoundState)")

    def n_active_players(self):
        return len(self.active_players())

    def active_players(self):
        return [p for p in self.current_players if not (p.prstate.folded or p.prstate.all_in)]

    def non_folded_players(self):
        return [p for p in self.current_players if not p.prstate.folded]

    def folded_players(self):
        return [p for p in self.current_players if p.prstate.folded]

    def all_in_players(self):
        return [p for p in self.current_players if p.prstate.all_in]

    # @property
    # def small_blind(self):
    #     return self.current_players[self.sm_blind_index]
    #
    # @property
    # def big_blind(self):
    #     self.big_blind_index = (self.sm_blind_index + 1) % len(self.current_players)
    #     return self.current_players[self.big_blind_index]

    @property
    def turn_player(self):
        return self.current_players[self.player_index]

    def reveal_cards(self, n):
        open_cards = self.community_cards[:n]
        self.public_cards = cards_backend.CardSet(open_cards + (5-n)*[cards_backend.Card(0, 0)])

    async def send_community_cards(self, channel):
        await self.public_cards.send_to(channel)

    def pot_amount(self):
        return sum([p.prstate.invested for p in self.current_players])

