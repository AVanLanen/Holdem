# game/views.py

import json
import sys
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Game, GameRound, Player
from . import game_logic

import logging

@login_required
def game_view(request):
    player = Player.objects.get(user=request.user)
    active_game = Game.objects.filter(players=player, status='active').first()
    
    if active_game:
        return redirect('game_action', game_id=active_game.id)
    
    available_games = Game.objects.filter(status='waiting')
    return render(request, 'game/lobby.html', {'available_games': available_games})

@login_required
def start_game(request):
    player = Player.objects.get(user=request.user)
    game = Game.objects.create(status='waiting')
    game.players.add(player)
    return redirect('game_action', game_id=game.id)

@login_required
def join_game(request, game_id):
    player = Player.objects.get(user=request.user)
    game = get_object_or_404(Game, id=game_id)
    if game.status == 'waiting':
        game.players.add(player)
        if game.players.count() >= 2:  # You can adjust this number as needed
            game.status = 'active'
            game.save()
    return redirect('game_action', game_id=game.id)

@login_required
def game_action(request, game_id):
    player = Player.objects.get(user=request.user)
    game = get_object_or_404(Game, id=game_id)
    current_round = game.gameround_set.last()

    # Initialize game_state here, outside of any condition
    if not current_round or current_round.game_state.get('status') == 'completed':
        # Initialize a new round if one doesn't exist or the previous one is completed
        game_state = game_logic.init_game_round(list(game.players.all()))
        current_round = GameRound.objects.create(game=game, round_number=game.gameround_set.count() + 1, game_state=game_state)
    else:
        # Ensure we're working with the latest data
        current_round.refresh_from_db()
        game_state = current_round.game_state

    if request.method == 'POST':
        action = request.POST.get('action')
        logging.info(f"Received action: {action}")
        logging.info(f"Current game state before action: {game_state['status']}")

        if action == 'place_bets':
            ante_blind = int(request.POST.get('ante_blind', 0))
            trips = int(request.POST.get('trips', 0))
            game_state = game_logic.place_initial_bets(game_state, str(player.id), ante_blind, trips)
        elif action == 'check':
            game_state = game_logic.player_action(game_state, str(player.id), 'check')
        elif action == 'bet':
            multiplier = int(request.POST.get('multiplier', 0))
            game_state = game_logic.player_action(game_state, str(player.id), 'bet', multiplier)
        elif action == 'fold':
            game_state = game_logic.player_action(game_state, str(player.id), 'fold')

        current_round.game_state = game_state
        current_round.save()
        logging.info(f"Game state after action: {current_round.game_state['status']}")

        # Check if the game has reached showdown
        if game_state['status'] == 'showdown':
            return redirect('game_results', game_id=game.id)

    # Prepare context for template rendering
    player_hand = game_state['player_hands'].get(str(player.id), [])
    community_cards = game_state.get('community_cards', [])
    
    player_hand_description = ""
    if player_hand and community_cards:
        player_hand_description = game_logic.evaluate_hand(player_hand + community_cards)[2]

    context = {
        'game': game,
        'player': player,
        'current_round': current_round,
        'available_actions': game_logic.get_available_actions(game_state, str(player.id)),
        'player_hand_description': player_hand_description,
    }

    if request.htmx:
        return HttpResponse(render_to_string('game/game_container.html', context, request=request))
    else:
        return render(request, 'game/game.html', context)

@login_required
def place_initial_bets(request, game_id):
    player = Player.objects.get(user=request.user)
    game = get_object_or_404(Game, id=game_id)
    current_round = game.gameround_set.last()

    if request.method == 'POST':
        ante_blind = int(request.POST.get('ante_blind', 0))
        trips = int(request.POST.get('trips', 0))
        
        if ante_blind < game_logic.MIN_BET or ante_blind > game_logic.MAX_BET:
            return HttpResponse(f'Ante/Blind must be between {game_logic.MIN_BET} and {game_logic.MAX_BET}', status=400)
        
        if trips > 50:  # Assuming max trips bet is 50
            return HttpResponse('Trips bet cannot exceed 50', status=400)
        
        if ante_blind + trips > player.chips:
            return HttpResponse('Insufficient chips for this bet', status=400)
        
        game_state = current_round.game_state
        game_state = game_logic.place_initial_bets(game_state, str(player.id), ante_blind, trips)
        current_round.game_state = game_state
        current_round.save()
        
        player.chips -= (ante_blind * 2 + trips)  # Deduct ante, blind, and trips from player's chips
        player.save()
        
        context = {
            'game': game,
            'player': player,
            'current_round': current_round,
            'available_actions': game_logic.get_available_actions(game_state, str(player.id))
        }
        return HttpResponse(render_to_string('game/game_container.html', context, request=request))
    
    return HttpResponse('Invalid request', status=400)

@login_required
def start_new_round(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    players = game.players.all()
    
    # Initialize a new round
    game_state = game_logic.init_game_round(list(players))
    new_round = GameRound.objects.create(game=game, round_number=game.gameround_set.count() + 1, game_state=game_state)
    
    context = {
        'game': game,
        'player': request.user.player,
        'current_round': new_round,
        'available_actions': game_logic.get_available_actions(game_state, str(request.user.player.id))
    }
    
    return HttpResponse(render_to_string('game/game_container.html', context, request=request))

@login_required
def delete_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    
    if game.status == 'waiting':
        game.delete()
        response = HttpResponse(status=200)
        response['HX-Trigger'] = 'refreshGameList'
        return response
    else:
        return HttpResponse("Can't delete an active or completed game.", status=403)
@login_required
def game_results(request, game_id):
    player = get_object_or_404(Player, user=request.user)
    game = get_object_or_404(Game, id=game_id)
    current_round = game.gameround_set.last()
    game_state = current_round.game_state

    results, dealer_hand_description, dealer_best_hand, dealer_hole_cards = game_logic.resolve_round(game_state)

    # Process results to include bet details and payouts
    processed_results = {}
    for player_id, result in results.items():
        # Adjust the player's chip count based on their winnings or losses
        if player_id == str(player.id):
            player.chips += result['winnings']
            player.save()  # Save the updated chip count to the database

        processed_results[player_id] = {
            'winnings': result['winnings'],
            'hand': result['hand'],
            'hole_cards': result['hole_cards'],
            'cards': result.get('best_hand', []),  # Ensure cards contains the best hand
            'bets': game_state['player_bets'][player_id],
            'payouts': {
                'ante': result['payouts'].get('ante', 0),
                'blind': result['payouts'].get('blind', 0),
                'trips': result['payouts'].get('trips', 0),
                'play': result['payouts'].get('play', 0),
            }
        }

        print("processed", processed_results)
        # Print the winnings for each player
        print(f"Player {player_id} winnings: {result['winnings']}")
    
    context = {
        'game': game,
        'player': player,  # Add player to context
        'results': processed_results,
        'dealer_hand_description': dealer_hand_description,
        'dealer_best_hand': dealer_best_hand,
        'dealer_hole_cards': dealer_hole_cards,
        'community_cards': game_state['community_cards'],
        'dealer_wins': any(result['winnings'] < 0 for result in results.values()),
    }

    return render(request, 'game/results.html', context)