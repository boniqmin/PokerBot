import copy
import random
# import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
from PIL import Image
import discord
import time


def merge_images(filenames, formatting):
    images = [Image.open(filename) for filename in filenames]
    widths, heights = [], []
    for image in images:
        (width, height) = image.size
        widths.append(width + 40)
        heights.append(height)

    result_width = sum(widths)
    result_height = max(heights)

    result = Image.new('RGBA', (result_width, result_height))
    for i in range(len(widths)):
        result.paste(im=images[i], box=(sum(widths[:i]), 0))

    if 'scale' in formatting:  # discord rescales automatically, so this is useless
        scale = formatting['scale']
        result = result.resize((int(result.height*scale), int(result.width*scale)), Image.ANTIALIAS)
    return result


class Card:
    suitname = {0: '', 1: 'Diamonds', 2: 'Clubs', 3: 'Hearts', 4: 'Spades'}
    valuename = {0: 'back', 1: 'Low Ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
                 11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace'}  # default ace is 14, 1 is only in straights

    suitabr = {0: None, 1: 'D', 2: 'C', 3: 'H', 4: 'S'}
    suitemoji = {1: '♥️', 2: '♣', 3: '♦️', 4: '♠️'}
    valueabr = {0: 'back', 1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
                11: 'J', 12: 'Q', 13: 'K', 14: 'A'}  # low ace is now redundant

    def __init__(self, suit, value):
        if not (0 <= suit <= 4 and 0 <= value <= 14):
            raise ValueError("Invalid value(s) for card")
        if (suit == 0 and value != 0) or (value == 0 and suit != 0):    # 0,0 is back of a card, can't have just one 0
            raise ValueError("Either both or neither parameters must be 0")
        self.suit = suit
        self.value = value
        if self.value != 0:
            self.filename = './files/cards/' + str(self) + '.png'
        else:
            self.filename = './files/cards/back.png'

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    # def show(self):  # test function
    #     img = mpimg.imread(self.filename)
    #     plt.imshow(img)
    #     #plt.show()

    def __str__(self):
        if self.suit == 0:
            return 'back'
        return Card.valueabr[self.value] + Card.suitabr[self.suit]

    def emojiprint(self):
        if self.suit == 0:
            return ''
        return Card.suitemoji[self.suit] + Card.valueabr[self.value]

    def __repr__(self):
        return str(self)


# check helper functions
########################################################################################################################
def straight_mask(low_value):
    mask = []
    for i in range(5):
        mask.append(low_value + 4 - i)  # [4,3,2,1,0] + low_value for each element
    return mask


def list_diff(list1, list2):
    if len(list1) != len(list2):
        raise ValueError("Lists must have same length")
    return [list1[i] - list2[i] for i in range(len(list1))]


def find_n(n, card_values, more=False):  # returns cards value of the highest n-of a kind
    candidates = [0]                        # more parameter: is more than n cards also allowed?
    for i in range(2, 15):
        count = card_values.count(i)
        if count == n or (count >= n and more):
            candidates.append(i)
    return max(candidates)

# -------------------------------------------------------------------------------------------------------------------- #


# check functions
########################################################################################################################
# note: usage of term 'hand' is outdated, the param will in general be a CardSet object

def check_straight_flush(hand):
    suits = hand.suits
    flush_suit = 0
    for i in range(1, 5):
        if suits.count(i) >= 5:
            flush_suit = i
    if flush_suit == 0:  # no flush
        return False
    suit_cards = CardSet([card for card in hand.cards if card.suit == flush_suit])
    straight = check_straight(suit_cards)
    if not straight:
        return False

    straight_card_values = [card.value for card in straight[1:]]  # [1:] skips the hand code
    hand_code = 8  # straight flush
    if 14 in straight_card_values:
        hand_code = 9  # royal flush
    return [hand_code] + straight[1:]  # cards are the same, just hand code needs to be adjusted


def check_4oak(hand):
    fouroak_value = find_n(4, hand.values)
    four_oak = []     # Of A Kind
    remaining = []
    if fouroak_value == 0:
        return False
    else:
        for card in hand.cards:
            if card.value == fouroak_value:
                four_oak.append(card)
            else:
                remaining.append(card)
    return [7] + four_oak + [max(remaining)]  # 7 is hand code of 4oak


def check_full_house(hand):
    highest_pair_value = find_n(3, hand.values)  # find high triple. More than triple is automatically 4oak
    triple = []
    remaining1 = []
    if highest_pair_value == 0:
        return False
    else:
        for card in hand.cards:
            if card.value == highest_pair_value:
                triple.append(card)
            else:
                remaining1.append(card)

    remaining_values = [card.value for card in remaining1]
    highest_pair_value = find_n(2, remaining_values, more=True)   # find pair/lower triple in remaining cards.
    double = []
    remaining2 = []
    if highest_pair_value == 0:
        return False
    else:
        for card in remaining1:
            if card.value == highest_pair_value:
                double.append(card)
            else:
                remaining2.append(card)

    double = sorted(double, reverse=True)[:2]  # in case of a second triple
    return [6] + triple + double  # 2 is hand code of double pair


def check_flush(hand):
    # if len(hand.cards) < 5:   # redundant
    #     return False
    suits = hand.suits
    flush_suit = 0
    for i in range(1, 5):
        if suits.count(i) >= 5:
            flush_suit = i          # can't have multiple flushes of different suits in 7 cards

    if flush_suit == 0:
        return False
    else:
        flush_cards = []
        for card in hand.cards:
            if card.suit == flush_suit:
                flush_cards.append(card)
        return [5] + sorted(flush_cards, reverse=True)[:5]
        # 5 is hand code for flush. If there are more than 5 cards of a suit, take the highest 5


def check_straight(hand):
    cards = hand.cards
    if len(cards) < 5:
        return False

    carddict = {card.value: card for card in cards}  # duplicates automatically removed
    if len(carddict) < 5:  # if removing duplicates leaves less than 5 cards, no straight
        return False

    if 14 in carddict:  # add "low ace" since ace can act as lowest and highest card in straight
        ace_suit = carddict[14].suit
        carddict[1] = Card(ace_suit, 1)

    values = sorted(carddict.keys(), reverse=True)

    for i in range(len(values) - 5 + 1):  # -5 to find how many you can shift, + 1 for indexing purposes
        low_value = values[i + 4]  # 5th card is 4 spots further than "i"
        if list_diff(values[i:i + 5], straight_mask(low_value)).count(0) == 5:
            straight_cards = [carddict[v] for v in values[i:i+5]]
            return [4] + straight_cards  # 4 is hand code for straight
    return False


def check_3oak(hand):
    highest_3oak_value = find_n(3, hand.values)
    three_oak = []     # Of A Kind
    remaining = []
    if highest_3oak_value == 0:
        return False
    else:
        for card in hand.cards:
            if card.value == highest_3oak_value:
                three_oak.append(card)
            else:
                remaining.append(card)
    return [3] + three_oak + sorted(remaining, reverse=True)[:2]  # 3 is hand code of 3oak


def check_double_pair(hand):  # First check double pair, if yes skip pair
    highest_pair_value = find_n(2, hand.values)  # find high pair
    high_pair = []
    remaining1 = []
    if highest_pair_value == 0:
        return False
    else:
        for card in hand.cards:
            if card.value == highest_pair_value:
                high_pair.append(card)
            else:
                remaining1.append(card)

    remaining_values = [card.value for card in remaining1]
    highest_pair_value = find_n(2, remaining_values)   # find low pair in remaining cards
    low_pair = []
    remaining2 = []
    if highest_pair_value == 0:
        return False
    else:
        for card in remaining1:
            if card.value == highest_pair_value:
                low_pair.append(card)
            else:
                remaining2.append(card)
    return [2] + high_pair + low_pair + [max(remaining2)]  # 2 is hand code of double pair


def check_pair(hand):
    highest_pair_value = find_n(2, hand.values)
    pair = []
    remaining = []
    if highest_pair_value == 0:
        return False
    else:
        for card in hand.cards:
            if card.value == highest_pair_value:
                pair.append(card)
            else:
                remaining.append(card)
    return [1] + pair + sorted(remaining, reverse=True)[:3]  # 1 is hand code of pair


def check_high_card(hand):  # high card always exists, "check" for consistency
    return [0] + sorted(hand.cards, reverse=True)[:5]  # 0 is hand code for high card


def hand_value(hand):
    checks = [check_straight_flush, check_4oak, check_full_house,
              check_flush, check_straight, check_3oak, check_double_pair,
              check_pair, check_high_card]
    for check in checks:
        hv = check(hand)
        if hv:
            return hv

# -------------------------------------------------------------------------------------------------------------------- #


class CardSet:
    def __init__(self, cards):
        self.cards = cards

    async def save_image_to(self, path, formatting=None):
        if formatting is None:
            formatting = {}
        filenames = [card.filename for card in self.cards]
        image = merge_images(filenames, formatting)
        image.save(path)

    async def send_to(self, channel, caption=None, color=discord.Colour.from_rgb(254, 254, 254)):
        path = "./files/CardImgBuffer.png"
        await self.save_image_to(path)
        if caption is not None:
            caption = ''
        cards_embed = discord.Embed(title=caption, color=color)
        cardset_image = discord.File("./files/CardImgBuffer.png", "cardset.png")
        cards_embed.set_image(url="attachment://cardset.png")

        await channel.send(file=cardset_image, embed=cards_embed)

    # def show(self):  # test function
    #     handimg = merge_images(self.filenames())
    #     handimg.save("C:/Users/benja/PycharmProjects/PokerBot/hand.png")
    #     img = mpimg.imread("C:/Users/benja/PycharmProjects/PokerBot/hand.png")
    #     plt.imshow(img)
    #     plt.show()

    def filenames(self):
        return [card.filename for card in self.cards]

    @property
    def suits(self):
        return [card.suit for card in self.cards]

    @property
    def values(self):
        return [card.value for card in self.cards]

    def __add__(self, other):
        return CardSet(self.cards + other.cards)

    def __getitem__(self, item):
        return self.cards[item]

    def to_hand(self):
        return Hand(self.cards)


class Hand(CardSet):
    handnamedict = {-1: "undetermined", 0: "High card", 1: "Pair", 2: "Two pair", 3: "Three of a kind", 4: "Straight",
                    5: "Flush", 6: "Full house", 7: "Four of a kind", 8: "Straight flush", 9: "Royal flush"}

    def __init__(self, cards):  # TODO: keep cards as list?
        super().__init__(cards)
        self.cards.sort()
        self.handvalue = hand_value(self)
        self.handname = Hand.handnamedict[self.handvalue[0]]

    def __eq__(self, other):
        return self.handvalue == other.handvalue

    def __lt__(self, other):
        return self.handvalue < other.handvalue

    def __gt__(self, other):
        return self.handvalue > other.handvalue


def deck():
    deck_list = []
    for i in range(1, 5):
        for j in range(2, 15):
            deck_list.append(Card(i, j))
    return deck_list


def shuffled_deck():
    this_deck = deck()
    random.shuffle(this_deck)
    return this_deck
