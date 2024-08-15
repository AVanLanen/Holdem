import random
import itertools
from collections import Counter

# Constants
SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
MAX_PLAYERS = 6
MIN_BET = 10
MAX_BET = 300

# Paytables
BLIND_PAYTABLE = {
    'Royal Flush': 500,
    'Straight Flush': 50,
    'Quads': 10,
    'Full House': 3,
    'Flush': 1.5,
    'Straight': 1,
    'Other': 0
}

TRIPS_PAYTABLE = {
    'Royal Flush': 50,
    'Straight Flush': 40,
    'Quads': 30,
    'Full House': 8,
    'Flush': 7,
    'Straight': 4,
    'Three of a Kind': 3
}

# Card class
class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return f"{self.rank} of {self.suit}"

    def rank_value(self):
        return RANKS.index(self.rank)

# Deck class
class Deck:
    def __init__(self):
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, num=1):
        dealt_cards = []
        for _ in range(num):
            if len(self.cards) == 0:
                raise ValueError("No more cards in the deck")
            dealt_cards.append(self.cards.pop())
        return dealt_cards

# Player class
class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.hand = []
        self.ante = 0
        self.blind = 0
        self.trips = 0
        self.play_bet = 0
        self.folded = False

    def reset_bets(self):
        self.ante = 0
        self.blind = 0
        self.trips = 0
        self.play_bet = 0
        self.hand = []
        self.folded = False

    def place_ante_and_blind(self, amount):
        if amount > self.chips or amount < MIN_BET or amount > MAX_BET:
            raise ValueError(f"Ante and Blind bet must be between {MIN_BET} and {MAX_BET}, and within your chips.")
        self.ante = amount
        self.blind = amount
        self.chips -= (self.ante + self.blind)

    def place_trips_bet(self, amount):
        if amount > self.chips or amount < 1 or amount > 50:
            raise ValueError("Trips bet must be between 1 and 50 chips.")
        self.trips = amount
        self.chips -= self.trips

    def place_play_bet(self, multiplier):
        bet = self.ante * multiplier
        if bet > self.chips:
            raise ValueError("Insufficient chips for play bet")
        self.play_bet = bet
        self.chips -= bet

    def receive_cards(self, cards):
        self.hand.extend(cards)

    def fold(self):
        self.folded = True

    def __str__(self):
        return f"Player {self.name} with {self.chips} chips"

# Utility functions for hand evaluation
def evaluate_hand(cards):
    values = sorted([card.rank_value() for card in cards], reverse=True)
    suits = [card.suit for card in cards]
    counts = Counter(values)
    
    # Check for straight and flush
    is_flush = len(set(suits)) == 1
    is_straight = len(counts) == 5 and (values[0] - values[-1] == 4)
    
    if is_straight and is_flush:
        if values[0] == RANKS.index('A') and values[-1] == RANKS.index('10'):
            return (9, values, f"Royal Flush, {suits[0]}")
        return (8, values, f"Straight Flush, {RANKS[values[-1]]} through {RANKS[values[0]]} of {suits[0]}")
    if 4 in counts.values():
        four_of_a_kind = [value for value, count in counts.items() if count == 4]
        kicker = [value for value in values if value not in four_of_a_kind]
        return (7, four_of_a_kind + kicker, f"Quads, {RANKS[four_of_a_kind[0]]}s")
    if 3 in counts.values() and 2 in counts.values():
        three_of_a_kind = [value for value, count in counts.items() if count == 3]
        pair = [value for value, count in counts.items() if count == 2]
        return (6, three_of_a_kind + pair, f"Full House, {RANKS[three_of_a_kind[0]]}s over {RANKS[pair[0]]}s")
    if is_flush:
        return (5, values, f"Flush, {RANKS[values[0]]} high")
    if is_straight:
        return (4, values, f"Straight, {RANKS[values[-1]]} through {RANKS[values[0]]}")
    if 3 in counts.values():
        three_of_a_kind = [value for value, count in counts.items() if count == 3]
        kickers = [value for value in values if value not in three_of_a_kind]
        return (3, three_of_a_kind + kickers, f"Three of a Kind, {RANKS[three_of_a_kind[0]]}s")
    if list(counts.values()).count(2) == 2:
        pairs = [value for value, count in counts.items() if count == 2]
        kicker = [value for value in values if value not in pairs]
        return (2, sorted(pairs, reverse=True) + kicker, f"Two Pair, {RANKS[pairs[0]]}s and {RANKS[pairs[1]]}s")
    if 2 in counts.values():
        pair = [value for value, count in counts.items() if count == 2]
        kickers = [value for value in values if value not in pair]
        return (1, pair + kickers, f"Pair of {RANKS[pair[0]]}s")
    
    return (0, values, f"High Card, {RANKS[values[0]]}")

def best_five_card_hand(seven_cards):
    best_hand = None
    best_rank = (-1, [], "")
    for combination in itertools.combinations(seven_cards, 5):
        rank = evaluate_hand(combination)
        if rank > best_rank:
            best_rank = rank
            best_hand = combination
    return best_hand, best_rank

def calculate_winnings(player_rank, dealer_rank, player):
    total_bet = player.ante + player.blind + player.play_bet + player.trips
    # Blind bet payout
    hand_type = player_rank[2].split(",")[0]  # e.g., "Royal Flush", "Straight Flush"
    if player_rank > dealer_rank:
        blind_payout = BLIND_PAYTABLE.get(hand_type, BLIND_PAYTABLE['Other']) * player.blind
        ante_payout = player.ante + player.play_bet  # Ante and Play bets pay 1:1
        player.chips += ante_payout + blind_payout + total_bet  # Return the initial bet plus winnings
        print(f"{player.name} wins {ante_payout} from Ante and Play bets and {blind_payout} from Blind bet.")
    elif player_rank < dealer_rank:
        print(f"{player.name} loses all bets.")
    else:
        # Push condition
        player.chips += total_bet  # Return the initial bet (Push)
        print(f"{player.name}'s Ante, Blind, and Play bets are pushed.")
        if hand_type != "High Card":
            blind_payout = BLIND_PAYTABLE.get(hand_type, BLIND_PAYTABLE['Other']) * player.blind
            player.chips += blind_payout
            print(f"{player.name} wins {blind_payout} from Blind bet.")
    
    # Trips bet payout
    if player.trips > 0:
        trips_payout = TRIPS_PAYTABLE.get(hand_type, 0) * player.trips
        player.chips += trips_payout
        print(f"{player.name} wins {trips_payout} from Trips bet.")

# Game class
class UltimateTexasHoldem:
    def __init__(self, num_players):
        if num_players > MAX_PLAYERS:
            raise ValueError(f"Maximum {MAX_PLAYERS} players are allowed.")
        self.deck = Deck()
        self.players = []
        for i in range(num_players):
            name = input(f"Enter name for Player {i + 1}: ")
            chips = int(input(f"Enter starting chips for {name}: "))
            self.players.append(Player(name, chips))
        self.dealer = Player("Dealer", 0)
        self.community_cards = []

    def reset_round(self):
        self.deck = Deck()
        for player in self.players:
            player.reset_bets()
        self.community_cards = []
        self.dealer.hand = []

    def deal_initial_hands(self):
        for _ in range(2):  # Deal 2 cards to each player
            for player in self.players:
                player.receive_cards(self.deck.deal(1))
            self.dealer.receive_cards(self.deck.deal(1))

    def deal_community_cards(self, num):
        self.community_cards.extend(self.deck.deal(num))

    def show_community_cards(self):
        print("Community Cards: " + ", ".join(str(card) for card in self.community_cards))

    def player_initial_bets(self, player):
        print(f"{player.name}'s turn to place bets")
        ante_blind = int(input(f"{player.name}, enter your Ante and Blind bet (10-300): "))
        player.place_ante_and_blind(ante_blind)
        trips_bet = int(input(f"{player.name}, enter your Trips bet (1-50, or 0 to skip): "))
        if trips_bet > 0:
            player.place_trips_bet(trips_bet)
        print(f"{player.name} placed an Ante and Blind bet of {ante_blind} chips and a Trips bet of {trips_bet} chips.")

    def player_action_pre_flop(self, player):
        print(f"{player.name}'s turn")
        print(f"Your hand: {', '.join(str(card) for card in player.hand)}")
        action = input("Choose action: '4', '3', 'C': ").lower()
        if action in ['4', '3']:
            multiplier = int(action)
            player.place_play_bet(multiplier)
            print(f"{player.name} placed a {multiplier}x play bet of {player.play_bet} chips.")
        elif action in ['c', 'check']:
            print(f"{player.name} checked.")
        elif action in ['f', 'fold']:
            player.fold()
            print(f"{player.name} folded.")
        else:
            print("Invalid action. Defaulting to 'check'.")
            action = 'c'
        return action

    def player_action_after_flop(self, player):
        if player.play_bet == 0:  # Player checked pre-flop
            action = input(f"{player.name}, choose action: '2' or 'C': ").lower()
            if action == '2':
                player.place_play_bet(2)
                print(f"{player.name} placed a 2x play bet of {player.play_bet} chips.")
            elif action in ['c', 'check']:
                print(f"{player.name} checked.")
            else:
                print("Invalid action. Defaulting to 'check'.")
                action = 'c'
            return action

    def player_action_final(self, player):
        if player.play_bet == 0:  # Player checked both pre-flop and after flop
            action = input(f"{player.name}, choose action: '1' or 'F': ").lower()
            if action == '1':
                player.place_play_bet(1)
                print(f"{player.name} placed a 1x play bet of {player.play_bet} chips.")
            elif action in ['f', 'fold']:
                player.fold()
                print(f"{player.name} folded.")
            else:
                print("Invalid action. Defaulting to 'fold'.")
                player.fold()
            return action

    def determine_winners(self):
        dealer_best_hand, dealer_rank = best_five_card_hand(self.community_cards + self.dealer.hand)
        print(f"Dealer's hand: {', '.join(str(card) for card in self.dealer.hand)}")
        print(f"Dealer's best hand: {', '.join(str(card) for card in dealer_best_hand)} ({dealer_rank[2]})")

        for player in self.players:
            if player.folded:
                print(f"{player.name} folded and is out of this round.")
                continue
            
            player_best_hand, player_rank = best_five_card_hand(self.community_cards + player.hand)
            print(f"{player.name}'s best hand: {', '.join(str(card) for card in player_best_hand)} ({player_rank[2]})")

            calculate_winnings(player_rank, dealer_rank, player)

    def play_round(self):
        # Initial ante, blind, and trips bets
        for player in self.players:
            self.player_initial_bets(player)
        self.deal_initial_hands()

        # First betting round (Pre-Flop)
        for player in self.players:
            self.player_action_pre_flop(player)

        # Flop
        self.deal_community_cards(3)
        self.show_community_cards()

        # Second betting round (After Flop)
        for player in self.players:
            self.player_action_after_flop(player)

        # Turn
        self.deal_community_cards(1)
        self.show_community_cards()

        # River
        self.deal_community_cards(1)
        self.show_community_cards()

        # Final betting round (After River)
        for player in self.players:
            if player.play_bet == 0 and not player.folded:
                self.player_action_final(player)

        # Reveal dealer's cards and determine winners
        self.determine_winners()

    def play_game(self):
        while True:
            self.play_round()
            print("\nChip counts after this round:")
            for player in self.players:
                print(f"{player.name}: {player.chips} chips")
            if input("Play another round? (y/n): ").lower() != 'y':
                break
            self.reset_round()

def main():
    num_players = int(input("Enter number of players: "))
    game = UltimateTexasHoldem(num_players)
    game.play_game()

if __name__ == "__main__":
    main()
