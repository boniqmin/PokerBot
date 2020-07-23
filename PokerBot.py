import copy
import random
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import discord


# def merge_images(save_filename, *filenames):
#     images = [Image.open(filename) for filename in filenames]
#     widths, heights = [], []
#     for image in images:
#         (width, height) = image.size
#         widths.append(width+40)
#         heights.append(height)
#
#     result_width = sum(widths)
#     result_height = max(heights)
#
#     result = Image.new('RGBA', (result_width, result_height))
#     for i in range(len(widths)):
#         result.paste(im=images[i], box=(sum(widths[:i]), 0))
#     result.save(save_filename)

def merge_images(filenames):
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

    return result

class Card:
    suitname = {0: '', 1: 'Diamonds', 2: 'Clubs', 3: 'Hearts', 4: 'Spades'}
    valuename = {0: 'back', 1: 'Low Ace', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
                 11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace'}  # default ace is 14, 1 is only in straights

    suitabr = {0: None, 1: 'D', 2: 'C', 3: 'H', 4: 'S'}
    valueabr = {0: 'back', 1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
                 11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

    def __init__(self, suit, value):
        if not (0 <= suit <= 4 and 0 <= value <= 14):
            raise ValueError("Invalid value(s) for card")
        if (suit == 0 and value != 0) or (value == 0 and suit != 0):    # 0,0 is back of a card, can't have just one 0
            raise ValueError("Either both or neither parameters must be 0")
        self.suit = suit
        self.value = value
        if self.value != 0:
            self.filename = 'C:/Users/benja/PycharmProjects/PokerBot/cards/' + str(self) + '.png'
        else:
            self.filename = 'C:/Users/benja/PycharmProjects/PokerBot/cards/back.png'

    def __gt__(self, other):
        return self.value > other.value

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    def show(self):  # test function
        img = mpimg.imread(self.filename)
        plt.imshow(img)
        #plt.show()

    def __str__(self):
        return Card.valueabr[self.value] + Card.suitabr[self.suit]

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

def check_straight_flush(hand): # also checks for royal (maybe integrate normal straight?)
    cards = copy.copy(hand.cards)  # (1)aces should only be added to a copy
    values = hand.values
    for card in cards:  # Ace acts as highest and lowest, so if (14)ace in hand, add a (1)ace
        if card.value == 14:  # ace
            cards.append(Card(1, 1))  # suit is irrelevant
            values.append(1)
            break   # multiple aces are irrelevant

    values = sorted(values, reverse=True)  # check from high to low
    cards = sorted(cards, reverse=True)
    for i in range(len(cards) - 5 + 1):  # -5 to find how many you can shift, + 1 for indexing purposes
        continue_loop = False
        low_value = values[i+4]
        if list_diff(values[i:i+5], straight_mask(low_value)).count(0) == 5:

            straight_cards = cards[i:i+5]
            flush_suit = straight_cards[0].suit
            for card in straight_cards:         # if a straight is found, check if all the same suit
                if card.suit != flush_suit:
                    continue_loop = True
                    break  # if not all the same suit, check for other straights

            if continue_loop:
                continue

            hand_code = 8  # straight flush
            for card in straight_cards:
                if card.value == 14:
                    hand_code = 9    # royal flush

            return [hand_code] + sorted(straight_cards, reverse=True)
    return False


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


def check_full_house(hand): # First check double pair, if yes skip pair
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
    if len(hand.cards) < 5:
        return False
    suits = hand.suits
    flush_suit = 0
    for i in range(1,5):
        if suits.count(i) >= 5:
            flush_suit = i          # can't have multiple flushes of different suits in 7 cards

    if flush_suit == 0:
        return False
    else:
        flush_cards = []
        for card in hand.cards:
            if card.suit == flush_suit:
                flush_cards.append(card)
        return [5] + sorted(flush_cards, reverse=True)[:5]  # 5 is hand code for flush. If there are more than 5 cards of a suit, take the highest 5


def check_straight(hand):
    cards = copy.copy(hand.cards)  #(1) aces should only be added to a copy
    values = hand.values
    for card in cards: # Ace acts as highest and lowest, so if (14)ace in hand, add a (1)ace
        if card.value == 14:  # ace
            cards.append(Card(1, 1))  # suit is irrelevant
            values.append(1)
            break   # multiple aces are irrelevant

    values = sorted(values, reverse=True)  # check from high to low
    cards = sorted(cards, reverse=True)
    for i in range(len(cards) - 4):  # -5 to find how many you can shift, + 1 for indexing purposes
        low_value = values[i+4]
        if list_diff(values[i:i+5], straight_mask(low_value)).count(0) == 5:

            straight_cards = cards[i:i+5]
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
    # handvalues = [check_straight_flush(hand), check_4oak(hand), check_full_house(hand),
    #               check_flush(hand), check_straight(hand), check_3oak(hand), check_double_pair(hand),
    #               check_pair(hand), check_high_card(hand)]
    # for hv in handvalues:
    #     if hv:
    #         return hv

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

    async def send_to(self, channel):
        filenames = [card.filename for card in self.cards]
        image = merge_images(filenames)
        path = "C:/Users/benja/PycharmProjects/PokerBot/CardImgBuffer.png"
        image.save(path)
        await channel.send(file=discord.File(path))

    def show(self):
        handimg = merge_images(self.filenames())
        handimg.save("C:/Users/benja/PycharmProjects/PokerBot/hand.png")
        img = mpimg.imread("C:/Users/benja/PycharmProjects/PokerBot/hand.png")
        plt.imshow(img)
        plt.show()

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
