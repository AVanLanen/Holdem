from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(str(key))

@register.filter
def range_filter(value):
    return range(value)

@register.filter
def card_image(card, show=True):
    if not show or card == '?':
        return 'game/assets/normal_cards/cardBackRed.png'
    
    rank, suit = card.split(' of ')
    
    if rank in ['Jack', 'Queen', 'King']:
        file_rank = rank[0]
    elif rank == 'Ace':
        file_rank = 'A'
    else:
        file_rank = rank
    
    suit = suit.capitalize()
    
    return f'game/assets/normal_cards/individual/{suit.lower()}/card{suit}_{file_rank}.png'