# game/game_logic.py

import logging
import random
from collections import Counter
from itertools import combinations

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
    'Other': 1
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

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

    def __str__(self):
        return f"{self.rank} of {self.suit}"

def create_deck():
    return [str(Card(suit, rank)) for suit in SUITS for rank in RANKS]

def deal_cards(deck, num):
    return [deck.pop() for _ in range(num)]

def init_game_round(players):
    game_state = {
        'player_bets': {str(player.id): {'ante': 0, 'blind': 0, 'trips': 0, 'play': 0, 'folded': False} for player in players},
        'player_hands': {str(player.id): [] for player in players},
        'dealer_hand': [],
        'community_cards': [],
        'status': 'betting',
        'deck': create_deck()
    }
    return game_state

def place_initial_bets(game_state, player_id, ante_blind, trips):
    player_id = str(player_id)
    game_state['player_bets'][player_id]['ante'] = ante_blind
    game_state['player_bets'][player_id]['blind'] = ante_blind
    game_state['player_bets'][player_id]['trips'] = trips
    
    # Check if all players have placed their bets
    if all(bets['ante'] > 0 for bets in game_state['player_bets'].values()):
        game_state = deal_initial_cards(game_state)
    
    return game_state

def deal_initial_cards(game_state):
    deck = create_deck()
    random.shuffle(deck)
    game_state['player_hands'] = {player_id: deal_cards(deck, 2) for player_id in game_state['player_bets'].keys()}
    game_state['dealer_hand'] = deal_cards(deck, 2)
    game_state['deck'] = deck
    game_state['community_cards'] = []
    game_state['status'] = 'pre_flop'
    return game_state

def player_action(game_state, player_id, action, bet_multiplier=0):
    player_id = str(player_id)
    logging.info(f"Player {player_id} action: {action}. Current game state: {game_state['status']}")
    
    if action == 'check':
        print(f"Player {player_id} checked. Current state: {game_state['status']}")
        game_state['player_bets'][player_id]['checked'] = True
    
    elif action == 'bet':
        ante = game_state['player_bets'][player_id]['ante']
        game_state['player_bets'][player_id]['play'] = ante * bet_multiplier
        logging.info(f"Player {player_id} bet {ante * bet_multiplier}.")
        return move_to_showdown(game_state)
    
    elif action == 'fold':
        game_state['player_bets'][player_id]['folded'] = True
        logging.info(f"Player {player_id} folded.")
    
    # Check if all players have acted
    all_acted = all(
        player['folded'] or player['play'] > 0 or player.get('checked', False) 
        for player in game_state['player_bets'].values()
    )
    
    if all_acted:
        print(f"All players have acted. Current state: {game_state['status']}")
        if game_state['status'] == 'pre_flop':
            game_state = move_to_next_stage(game_state, 'flop')
        elif game_state['status'] == 'flop':
            game_state = move_to_next_stage(game_state, 'turn_river')
        elif game_state['status'] == 'turn_river':
            game_state = move_to_showdown(game_state)
    
    logging.info(f"New game state after action: {game_state['status']}")
    return game_state

def move_to_showdown(game_state):
    # Deal remaining community cards if necessary
    cards_to_deal = 5 - len(game_state['community_cards'])
    if cards_to_deal > 0:
        game_state['community_cards'].extend(deal_cards(game_state['deck'], cards_to_deal))
    game_state['status'] = 'showdown'
    logging.info("Moving to showdown.")
    return game_state

def move_to_next_stage(game_state, next_stage):
    print(f"Moving to next stage: {next_stage}")
    if next_stage == 'flop':
        game_state['community_cards'].extend(deal_cards(game_state['deck'], 3))
        game_state['status'] = 'flop'
    elif next_stage == 'turn_river':
        game_state['community_cards'].extend(deal_cards(game_state['deck'], 2))
        game_state['status'] = 'turn_river'
    
    # Reset 'checked' status for all players
    for player_bets in game_state['player_bets'].values():
        player_bets['checked'] = False
    
    logging.info(f"New game state: {game_state['status']}")
    return game_state

def move_to_showdown(game_state):
    # Deal remaining community cards
    cards_to_deal = 5 - len(game_state['community_cards'])
    game_state['community_cards'].extend(deal_cards(game_state['deck'], cards_to_deal))
    game_state['status'] = 'showdown'
    return game_state

def evaluate_hand(cards):
    card_objects = [Card(card.split(' of ')[1], card.split(' of ')[0]) for card in cards]
    ranks = [RANKS.index(card.rank) for card in card_objects]
    suits = [card.suit for card in card_objects]
    rank_counts = Counter(ranks)

    is_flush = len(set(suits)) == 1
    ranks = sorted(set(ranks))  # Sort and remove duplicates
    is_straight = len(ranks) == 5 and (max(ranks) - min(ranks) == 4 or ranks == [0, 1, 2, 3, 12])

    hand_description = ""
    blind_hand_type = "Other"  # Default to "Other"

    if is_straight and is_flush:
        if ranks == [0, 1, 2, 3, 12]:
            hand_description = "Straight Flush - 5 high (Ace low)"
            blind_hand_type = "Straight Flush"
            return (8, ranks, hand_description, blind_hand_type)
        if max(ranks) == RANKS.index('A'):
            hand_description = "Royal Flush"
            blind_hand_type = "Royal Flush"
            return (9, sorted(ranks, reverse=True), hand_description, blind_hand_type)
        hand_description = f"Straight Flush - {RANKS[max(ranks)]} high"
        blind_hand_type = "Straight Flush"
        return (8, sorted(ranks, reverse=True), hand_description, blind_hand_type)
    elif 4 in rank_counts.values():
        four_of_a_kind = [r for r, c in rank_counts.items() if c == 4][0]
        hand_description = f"Quads - {RANKS[four_of_a_kind]}s"
        blind_hand_type = "Quads"
        return (7, [four_of_a_kind] + sorted([r for r in ranks if r != four_of_a_kind], reverse=True), hand_description, blind_hand_type)
    elif 3 in rank_counts.values() and 2 in rank_counts.values():
        three_of_a_kind = [r for r, c in rank_counts.items() if c == 3][0]
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        hand_description = f"Full House - {RANKS[three_of_a_kind]}s over {RANKS[pair]}s"
        blind_hand_type = "Full House"
        return (6, [three_of_a_kind] + [pair], hand_description, blind_hand_type)
    elif is_flush:
        hand_description = f"Flush - {RANKS[max(ranks)]} high"
        blind_hand_type = "Flush"
        return (5, sorted(ranks, reverse=True), hand_description, blind_hand_type)
    elif is_straight:
        if ranks == [0, 1, 2, 3, 12]:
            hand_description = "Straight - 5 high (Ace low)"
            blind_hand_type = "Straight"
            return (4, ranks, hand_description, blind_hand_type)
        hand_description = f"Straight - {RANKS[max(ranks)]} high"
        blind_hand_type = "Straight"
        return (4, sorted(ranks, reverse=True), hand_description, blind_hand_type)
    elif 3 in rank_counts.values():
        three_of_a_kind = [r for r, c in rank_counts.items() if c == 3][0]
        hand_description = f"Three of a Kind - {RANKS[three_of_a_kind]}s"
        return (3, [three_of_a_kind] + sorted([r for r in ranks if r != three_of_a_kind], reverse=True), hand_description, blind_hand_type)
    elif list(rank_counts.values()).count(2) == 2:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        hand_description = f"Two Pair - {RANKS[pairs[0]]}s and {RANKS[pairs[1]]}s"
        return (2, pairs + sorted([r for r in ranks if rank_counts[r] == 1], reverse=True), hand_description, blind_hand_type)
    elif 2 in rank_counts.values():
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        hand_description = f"One Pair - {RANKS[pair]}s"
        return (1, [pair] + sorted([r for r in ranks if r != pair], reverse=True), hand_description, blind_hand_type)
    else:
        hand_description = f"High Card - {RANKS[max(ranks)]}"
        return (0, sorted(ranks, reverse=True), hand_description, blind_hand_type)


def best_five_card_hand(seven_cards):
    best_hand = None
    best_value = (-1, [], "")
    for five_cards in combinations(seven_cards, 5):
        hand_value = evaluate_hand(five_cards)
        if hand_value > best_value:
            best_value = hand_value
            best_hand = five_cards
    return best_hand, best_value

def resolve_round(game_state):
    results = {}
    community_cards = game_state['community_cards']
    dealer_hand = game_state['dealer_hand']
    dealer_best_hand, dealer_rank = best_five_card_hand(community_cards + dealer_hand)
    
    print("\n=== Round Resolution ===")
    print(f"Community Cards: {', '.join(community_cards)}")
    print(f"Dealer's Hand: {', '.join(dealer_hand)}")
    print(f"Dealer's Best Hand: {dealer_rank[2]} ({', '.join(dealer_best_hand)})")
    
    for player_id, player_data in game_state['player_hands'].items():
        print(f"\n--- Resolving for Player {player_id} ---")
        print(f"Player's Hand: {', '.join(player_data)}")
        player_bets = game_state['player_bets'][player_id]
        print(f"Player's Bets: Ante: ${player_bets['ante']}, Blind: ${player_bets['blind']}, Trips: ${player_bets['trips']}, Play: ${player_bets['play']}")
        
        if player_bets.get('folded', False):
            # Handle fold: calculate loss
            net_loss = calculate_folded_result(player_bets)
            results[player_id] = {
                'winnings': net_loss,
                'hand': None,
                'best_hand': None,
                'hole_cards': player_data,
                'bets': player_bets,
                'payouts': {
                    'ante': 0,
                    'blind': 0,
                    'trips': 0,
                    'play': 0
                },
                'total_payout': 0,
                'total_bet': sum(player_bets.values())
            }
        else:
            player_best_hand, player_rank = best_five_card_hand(community_cards + player_data)
            print(f"Player's Best Hand: {player_rank[2]} ({', '.join(player_best_hand)})")
            
            winnings_info = calculate_winnings(player_rank, dealer_rank, player_bets)
            print("winnings_info", winnings_info)
            results[player_id] = {
                'winnings': winnings_info['net_result'],
                'hand': player_rank[2],
                'best_hand': player_best_hand,
                'hole_cards': player_data,
                'bets': player_bets,
                'payouts': winnings_info['payouts'],
                'total_payout': winnings_info['total_payout'],
                'total_bet': winnings_info['total_bet']
            }
    
    return results, dealer_rank[2], dealer_best_hand, dealer_hand


def calculate_folded_result(player_bets):
    return -(player_bets['ante'] + player_bets['blind'] + player_bets['trips'])

def calculate_winnings(player_rank, dealer_rank, player_bets):
    print("\n--- Detailed Winnings Calculation ---")
    print(f"Original bets: Ante: ${player_bets['ante']}, Blind: ${player_bets['blind']}, Trips: ${player_bets['trips']}, Play: ${player_bets['play']}")

    total_bet = sum(player_bets.values())
    print(f"Total bet: ${total_bet}")

    winnings = 0
    net_result = 0
    payouts = {
        'ante': 0,
        'blind': 0,
        'trips': 0,
        'play': 0
    }
    hand_type = player_rank[2]
    blind_hand_type = player_rank[3]  # Use the new blind_hand_type variable
    dealer_hand_type = dealer_rank[2]
    print(f"Player's hand: {hand_type}")
    print(f"Dealer's hand: {dealer_hand_type}")

    # Check if dealer qualifies (has at least a pair)
    dealer_qualifies = dealer_rank[0] >= 1  # 1 is the value for One Pair in our ranking system
    print(f"Dealer qualifies: {'Yes' if dealer_qualifies else 'No'}")

    if player_rank > dealer_rank:
        print("Player wins!")

        # Ante bet
        if dealer_qualifies:
            ante_win = player_bets['ante']
            payouts['ante'] = ante_win
            print("payouts ante", payouts['ante'])
            winnings += ante_win
            print("paying ante bet", winnings)
        else:
            print("Dealer doesn't qualify. Ante bet pushes.")
            payouts['ante'] = 0

        # Play bet
        play_win = player_bets['play']
        payouts['play'] = play_win
        print("payouts play",payouts['play'])
        winnings += play_win
        print("paying play bet", winnings)

        # Blind bet
        if blind_hand_type != "Other":
            blind_multiplier = BLIND_PAYTABLE.get(blind_hand_type, 1)
            blind_win = player_bets['blind'] * blind_multiplier
            payouts['blind'] = blind_win
            winnings += blind_win
            print("paying blind bet", winnings)
        else:
            print("Player's hand is 'Other'. Blind bet pushes (returned to player).")
            payouts['blind'] = 0

        print(f"Subtotal winnings (Ante + Play + Blind): ${winnings}")
        net_result = winnings  # Net result excludes pushed bets

    elif player_rank < dealer_rank:
        print("Dealer wins. Player loses all bets.")
        net_result = -total_bet  # Net loss is the total bet
        winnings = 0  # No winnings

    else:
        print("It's a tie!")
        print("Ante, Blind, and Play bets push (returned to player)")
        payouts['ante'] = player_bets['ante']
        payouts['blind'] = player_bets['blind']
        payouts['play'] = player_bets['play']
        net_result = 0  # No net gain or loss

    # Trips bet payout (always paid regardless of win/loss against dealer)
    if player_bets['trips'] > 0:
        trips_multiplier = TRIPS_PAYTABLE.get(hand_type, 0)
        trips_win = player_bets['trips'] * trips_multiplier
        payouts['trips'] = trips_win
        winnings += trips_win
        net_result += trips_win  # Add trips payout to the net result

    print(f"Total winnings (before subtracting original bets): ${winnings}")
    print(f"Net win/loss: ${net_result}")
    print("payouts" ,payouts)
    return {
        'net_result': net_result,  # Net result, which can be positive or negative
        'payouts': payouts,  # Detailed payout information
        'total_payout': winnings,  # Total amount won before subtracting bets
        'total_bet': total_bet  # Total amount bet
    }


def get_available_actions(game_state, player_id):
    player_id = str(player_id)
    if game_state['status'] == 'betting':
        return ['place_bets']
    elif player_id not in game_state['player_bets']:
        return []  # Player not in the game
    if game_state['player_bets'][player_id]['folded']:
        return []
    if game_state['player_bets'][player_id]['play'] > 0:
        return []
    if game_state['status'] == 'pre_flop':
        return ['check', 'bet_3x', 'bet_4x']
    elif game_state['status'] == 'flop':
        return ['check', 'bet_2x']
    elif game_state['status'] == 'turn_river':
        return ['bet_1x', 'fold']
    else:
        return []