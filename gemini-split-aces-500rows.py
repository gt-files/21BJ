import random
import time

# If you use colorama for colors in a console
try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    # If colorama isn't installed, define dummy Fore/Style
    class _DummyColors:
        def __getattr__(self, name):
            return ''
    Fore = Style = _DummyColors()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 1
SIMULATIONS = 30000
RTP = 0.995
ALLOW_DRAW_AFTER_SPLITTING_ACES = False  # or False, depending on your desired rule

ALL_RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']

RANK_TO_NAME = {
    '2': 'Twos',
    '3': 'Threes',
    '4': 'Fours',
    '5': 'Fives',
    '6': 'Sixes',
    '7': 'Sevens',
    '8': 'Eights',
    '9': 'Nines',
    'T': 'Tens',
    'J': 'Jacks',
    'Q': 'Queens',
    'K': 'Kings',
    'A': 'Aces'
}

RANK_TO_VALUE = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Card Counting System
COUNTING_SYSTEM = {
    '2': 1.0, '3': 1.0, '4': 2.0, '5': 2.0, '6': 2.0, '7': 1.0,
    '8': 0.0, '9': -1.0, 'T': -2.0, 'J': -2.0, 'Q': -2.0, 'K': -2.0, 'A': 0.0
}

# Global running count
running_count = 0


###############################################################################
# HELPER FUNCTIONS
###############################################################################
def initialize_shoe_counts(num_decks):
    shoe_counts = {}
    for rank in ALL_RANKS:
        shoe_counts[rank] = 4 * num_decks
    return shoe_counts

def print_shoe_status(shoe_counts, num_decks):
    print("\nCurrent Shoe Status:")
    for rank in reversed(ALL_RANKS):
        max_copies = 4 * num_decks
        current = shoe_counts[rank]
        rank_name = RANK_TO_NAME[rank]
        print(f" {rank_name}: {current} of {max_copies}")
    print("")

def remove_card_from_shoe(shoe_counts, rank):
    """
    Removes one instance of 'rank' from the global shoe_counts
    and adjusts the global running count accordingly.
    """
    global running_count
    if shoe_counts[rank] > 0:
        shoe_counts[rank] -= 1
        running_count += COUNTING_SYSTEM[rank]
    else:
        raise ValueError(f"Card '{rank}' not found (count is 0).")

def build_shoe_list(shoe_counts):
    """
    Returns a flat list of card *values* (2..11) repeated
    according to shoe_counts.
    """
    cards_list = []
    for rank in ALL_RANKS:
        count = shoe_counts[rank]
        val = RANK_TO_VALUE[rank]
        if count > 0:
            cards_list.extend([val] * count)
    return cards_list

def hand_value(cards):
    """
    Returns the best total <= 21 if possible, else the first bust total.
    Aces (11) may be downgraded to 1 if that helps.
    """
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces > 0:
        total -= 10
        aces -= 1
    return total

def is_soft_hand(cards):
    """
    Returns True if the hand is "soft"—meaning it contains
    at least one ace counted as 11 that still keeps the total <= 21.
    """
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces > 0:
        total -= 10
        aces -= 1
    # After adjusting for 'soft' aces, if any aces are left as 11, it's soft.
    return aces > 0

def simulate_dealer_hand_once(dealer_card_val, shoe_list):
    """
    Simulate a single dealer hand starting with dealer_card_val,
    drawing from a local copy of shoe_list. Returns the dealer's final total.
    """
    local_shoe = shoe_list.copy()
    # Remove the known dealer upcard from the local shoe
    if dealer_card_val in local_shoe:
        local_shoe.remove(dealer_card_val)
    dealer_cards = [dealer_card_val]
    
    while True:
        total = hand_value(dealer_cards)
        if total < DEALER_STAND and local_shoe:
            draw_val = random.choice(local_shoe)
            local_shoe.remove(draw_val)
            dealer_cards.append(draw_val)
        else:
            break
    return hand_value(dealer_cards)

def simulate_dealer_hands(dealer_card_val, shoe_counts, num_simulations):
    """
    Simulate the dealer's final totals num_simulations times,
    returning a list of final dealer totals.
    """
    shoe_list = build_shoe_list(shoe_counts)
    final_totals = []
    
    for _ in range(num_simulations):
        final_totals.append(simulate_dealer_hand_once(dealer_card_val, shoe_list))
    return final_totals

def process_results_for_stand_like(player_t, dealer_totals_list, is_soft):
    """
    Compare a standing player's total vs. many dealer totals.
    Returns the sum of +1 (win) / -1 (loss) / 0 (push).
    """
    if player_t > BLACKJACK:
        # If player is bust, all are lost
        return -1 * len(dealer_totals_list)
    
    chunk_ev = 0
    for d_total in dealer_totals_list:
        if d_total > BLACKJACK:
            chunk_ev += 1
        else:
            if is_soft:
                # If it's a soft hand, evaluate with Ace as 11
                soft_total = player_t + 10 if player_t <= 11 else player_t
                if soft_total > BLACKJACK:
                    if player_t > d_total:
                        chunk_ev += 1
                    elif player_t < d_total:
                        chunk_ev -= 1
                else:
                    if soft_total > d_total:
                        chunk_ev += 1
                    elif soft_total < d_total:
                        chunk_ev -= 1
            else:
                if player_t > d_total:
                    chunk_ev += 1
                elif player_t < d_total:
                    chunk_ev -= 1
    return chunk_ev

def calculate_insurance_ev(shoe_counts):
    """
    Roughly: Insurance pays 2:1 if dealer has blackjack (hidden 10-value).
    The bet costs 1 for every 2 gain in success.
    EV = P(BJ)*2 - (1 - P(BJ))*1
    """
    total_cards = sum(shoe_counts.values())
    ten_value_cards = shoe_counts['T'] + shoe_counts['J'] + shoe_counts['Q'] + shoe_counts['K']
    if total_cards == 0:
        return 0
    prob_dealer_blackjack = ten_value_cards / total_cards
    insurance_ev = (prob_dealer_blackjack * 2) - (1 - prob_dealer_blackjack)
    return insurance_ev

def print_dealer_probabilities(shoe_counts, dealer_up):
    """
    Example usage if you want to show whether insurance is profitable.
    """
    if dealer_up == 'A':
        insurance_ev = calculate_insurance_ev(shoe_counts)
        if insurance_ev < 0:
            print("Insurance bet is unprofitable")
        else:
            print("Insurance bet is profitable")


###############################################################################
# NEW HELPER FOR PLAYING OUT A HAND (for Hit or after Split)
###############################################################################
def play_out_hand(player_hand, local_deck, allow_double=True, force_one_draw=False):
    """
    Plays out the player's hand based on simple logic:
      - If allow_double is True and we have exactly 2 cards with total <= 11,
        we draw exactly one card and stop (bet_multiplier=2).
      - Otherwise, we keep drawing if total < 17 (or until bust/shoe empty).
      - If force_one_draw=True, we ensure at least one draw if we are "Hitting," 
        even if the hand starts at 17+ (which can reflect a real 'Hit' choice).
    Returns:
      (player_hand, bet_multiplier)
    """
    bet_multiplier = 1
    drawn_once = False

    # 1) Handle Doubling logic if allowed & exactly 2 cards
    if allow_double and len(player_hand) == 2:
        current_total = hand_value(player_hand)
        # Example: Double if total <= 11
        if current_total <= 11 and len(local_deck) > 0:
            bet_multiplier = 2
            # Draw exactly 1 card
            drawn_card = random.choice(local_deck)
            local_deck.remove(drawn_card)
            player_hand.append(drawn_card)
            return player_hand, bet_multiplier

    # 2) Otherwise, keep hitting while total < 17
    #    but also optionally force a single draw if force_one_draw=True
    while True:
        current_total = hand_value(player_hand)

        # If we haven't drawn yet and force_one_draw is True, draw exactly once
        if force_one_draw and not drawn_once:
            if not local_deck:
                break
            new_card = random.choice(local_deck)
            local_deck.remove(new_card)
            player_hand.append(new_card)
            drawn_once = True

            # If bust, stop
            if hand_value(player_hand) > 21:
                break

            # After forcing the one draw, continue to next iteration
            continue

        # Now do standard "hit until 17+" logic
        if current_total >= 17:
            break
        if not local_deck:
            break

        new_card = random.choice(local_deck)
        local_deck.remove(new_card)
        player_hand.append(new_card)

        if hand_value(player_hand) > 21:
            break

    return player_hand, bet_multiplier

###############################################################################
# MONTE CARLO EV FUNCTION (UPDATED)
###############################################################################
def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """
    Main Monte Carlo function that calculates EV for one action:
    'Stand', 'Hit', 'Double Down', or 'Split'.

    Each simulation uses a fresh local shoe. 
    The final EV is scaled by RTP.
    """
    start_time = time.time()
    player_total = hand_value(player_cards)
    is_soft_player = is_soft_hand(player_cards)
    ev = 0
    checkpoint_means = []

    # We break simulations into 10 chunks to measure convergence
    chunk_size = simulations // 10

    # -------------------------------------------------------------------------
    # STAND
    # -------------------------------------------------------------------------
    if action == "Stand":
        for i in range(10):
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = process_results_for_stand_like(player_total, dealer_totals, is_soft_player)
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # HIT (with full "play_out_hand" logic)
    # -------------------------------------------------------------------------
    elif action == "Hit":
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                # Copy shoe and remove known cards
                local_shoe = build_shoe_list(shoe_counts)

                # Remove player's known cards
                tmp_cards = []
                for val in player_cards:
                    if val in local_shoe:
                        local_shoe.remove(val)
                    tmp_cards.append(val)

                # Remove the dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # Now fully play out the player's hand, forcing at least one draw
                # and disallowing double for a plain "Hit."
                tmp_cards, bet_factor = play_out_hand(
                    tmp_cards,
                    local_shoe,
                    allow_double=False,     # because we explicitly said "Hit"
                    force_one_draw=True     # ensures we draw at least one card
                )
                p_total = hand_value(tmp_cards)

                # Dealer finishes
                d_total = simulate_dealer_hand_once(dealer_card_val, local_shoe)

                # Compare
                if p_total > BLACKJACK:
                    ev_chunk -= 1
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 1
                    elif p_total < d_total:
                        ev_chunk -= 1

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # DOUBLE DOWN (only one extra card, no further hitting)
    # -------------------------------------------------------------------------
    elif action == "Double Down":
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                local_shoe = build_shoe_list(shoe_counts)

                # Remove player's known cards
                tmp_cards = []
                for val in player_cards:
                    if val in local_shoe:
                        local_shoe.remove(val)
                    tmp_cards.append(val)

                # Remove dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # Take exactly one draw
                draw_val = random.choice(local_shoe) if local_shoe else 0
                if draw_val in local_shoe:
                    local_shoe.remove(draw_val)
                tmp_cards.append(draw_val)

                p_total = hand_value(tmp_cards)

                # Dealer final
                d_total = simulate_dealer_hand_once(dealer_card_val, local_shoe)

                # Compare (double => +/- 2)
                if p_total > BLACKJACK:
                    ev_chunk -= 2
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 2
                    elif p_total < d_total:
                        ev_chunk -= 2

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # SPLIT (DAS allowed)
    # -------------------------------------------------------------------------
    elif action == "Split":
        # The player's hand has exactly 2 cards of the same rank
        split_card_val = player_cards[0]
        split_ev_accumulator = 0

        # We have 2 sub-hands (since it's a split)
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                # Build a local shoe once per simulation
                local_shoe = build_shoe_list(shoe_counts)

                # Remove dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # --------- SUB-HAND #1 -----------
                sub_hand_1 = [split_card_val]
                if local_shoe:
                    draw_val = random.choice(local_shoe)
                    local_shoe.remove(draw_val)
                    sub_hand_1.append(draw_val)

                # Play out sub-hand 1
                sub_hand_1, bet_mult_1 = play_out_hand(
                    sub_hand_1,
                    local_shoe,
                    allow_double=True,
                    force_one_draw=False
                )
                p_total_1 = hand_value(sub_hand_1)

                # Dealer finishes for sub-hand 1
                d_total_1 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())

                # Resolve sub-hand 1
                if p_total_1 > BLACKJACK:
                    ev_sub_1 = -1 * bet_mult_1
                else:
                    if d_total_1 > BLACKJACK or p_total_1 > d_total_1:
                        ev_sub_1 = +1 * bet_mult_1
                    elif p_total_1 < d_total_1:
                        ev_sub_1 = -1 * bet_mult_1
                    else:
                        ev_sub_1 = 0

                # --------- SUB-HAND #2 -----------
                sub_hand_2 = [split_card_val]
                if local_shoe:
                    draw_val_2 = random.choice(local_shoe)
                    local_shoe.remove(draw_val_2)
                    sub_hand_2.append(draw_val_2)

                # Play out sub-hand 2
                sub_hand_2, bet_mult_2 = play_out_hand(
                    sub_hand_2,
                    local_shoe,
                    allow_double=True,
                    force_one_draw=False
                )
                p_total_2 = hand_value(sub_hand_2)

                # Dealer finishes for sub-hand 2
                d_total_2 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())

                # Resolve sub-hand 2
                if p_total_2 > BLACKJACK:
                    ev_sub_2 = -1 * bet_mult_2
                else:
                    if d_total_2 > BLACKJACK or p_total_2 > d_total_2:
                        ev_sub_2 = +1 * bet_mult_2
                    elif p_total_2 < d_total_2:
                        ev_sub_2 = -1 * bet_mult_2
                    else:
                        ev_sub_2 = 0

                # Combine results from both sub-hands
                ev_chunk += (ev_sub_1 + ev_sub_2)
 ठर
import random
import time

# If you use colorama for colors in a console
try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    # If colorama isn't installed, define dummy Fore/Style
    class _DummyColors:
        def __getattr__(self, name):
            return ''
    Fore = Style = _DummyColors()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 1
SIMULATIONS = 30000
RTP = 0.995
ALLOW_DRAW_AFTER_SPLITTING_ACES = False  # or False, depending on your desired rule

ALL_RANKS = ['2','3','4','5','6','7','8','9','T','J','Q','K','A']

RANK_TO_NAME = {
    '2': 'Twos',
    '3': 'Threes',
    '4': 'Fours',
    '5': 'Fives',
    '6': 'Sixes',
    '7': 'Sevens',
    '8': 'Eights',
    '9': 'Nines',
    'T': 'Tens',
    'J': 'Jacks',
    'Q': 'Queens',
    'K': 'Kings',
    'A': 'Aces'
}

RANK_TO_VALUE = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11
}

# Card Counting System
COUNTING_SYSTEM = {
    '2': 1.0, '3': 1.0, '4': 2.0, '5': 2.0, '6': 2.0, '7': 1.0,
    '8': 0.0, '9': -1.0, 'T': -2.0, 'J': -2.0, 'Q': -2.0, 'K': -2.0, 'A': 0.0
}

# Global running count
running_count = 0


###############################################################################
# HELPER FUNCTIONS
###############################################################################
def initialize_shoe_counts(num_decks):
    shoe_counts = {}
    for rank in ALL_RANKS:
        shoe_counts[rank] = 4 * num_decks
    return shoe_counts

def print_shoe_status(shoe_counts, num_decks):
    print("\nCurrent Shoe Status:")
    for rank in reversed(ALL_RANKS):
        max_copies = 4 * num_decks
        current = shoe_counts[rank]
        rank_name = RANK_TO_NAME[rank]
        print(f" {rank_name}: {current} of {max_copies}")
    print("")

def remove_card_from_shoe(shoe_counts, rank):
    """
    Removes one instance of 'rank' from the global shoe_counts
    and adjusts the global running count accordingly.
    """
    global running_count
    if shoe_counts[rank] > 0:
        shoe_counts[rank] -= 1
        running_count += COUNTING_SYSTEM[rank]
    else:
        raise ValueError(f"Card '{rank}' not found (count is 0).")

def build_shoe_list(shoe_counts):
    """
    Returns a flat list of card *values* (2..11) repeated
    according to shoe_counts.
    """
    cards_list = []
    for rank in ALL_RANKS:
        count = shoe_counts[rank]
        val = RANK_TO_VALUE[rank]
        if count > 0:
            cards_list.extend([val] * count)
    return cards_list

def hand_value(cards):
    """
    Returns the best total <= 21 if possible, else the first bust total.
    Aces (11) may be downgraded to 1 if that helps.
    """
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces > 0:
        total -= 10
        aces -= 1
    return total

def is_soft_hand(cards):
    """
    Returns True if the hand is "soft"—meaning it contains
    at least one ace counted as 11 that still keeps the total <= 21.
    """
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces > 0:
        total -= 10
        aces -= 1
    # After adjusting for 'soft' aces, if any aces are left as 11, it's soft.
    return aces > 0

def simulate_dealer_hand_once(dealer_card_val, shoe_list):
    """
    Simulate a single dealer hand starting with dealer_card_val,
    drawing from a local copy of shoe_list. Returns the dealer's final total.
    """
    local_shoe = shoe_list.copy()
    # Remove the known dealer upcard from the local shoe
    if dealer_card_val in local_shoe:
        local_shoe.remove(dealer_card_val)
    dealer_cards = [dealer_card_val]
    
    while True:
        total = hand_value(dealer_cards)
        if total < DEALER_STAND and local_shoe:
            draw_val = random.choice(local_shoe)
            local_shoe.remove(draw_val)
            dealer_cards.append(draw_val)
        else:
            break
    return hand_value(dealer_cards)

def simulate_dealer_hands(dealer_card_val, shoe_counts, num_simulations):
    """
    Simulate the dealer's final totals num_simulations times,
    returning a list of final dealer totals.
    """
    shoe_list = build_shoe_list(shoe_counts)
    final_totals = []
    
    for _ in range(num_simulations):
        final_totals.append(simulate_dealer_hand_once(dealer_card_val, shoe_list))
    return final_totals

def process_results_for_stand_like(player_t, dealer_totals_list, is_soft):
    """
    Compare a standing player's total vs. many dealer totals.
    Returns the sum of +1 (win) / -1 (loss) / 0 (push).
    """
    if player_t > BLACKJACK:
        # If player is bust, all are lost
        return -1 * len(dealer_totals_list)
    
    chunk_ev = 0
    for d_total in dealer_totals_list:
        if d_total > BLACKJACK:
            chunk_ev += 1
        else:
            if is_soft:
                # If it's a soft hand, evaluate with Ace as 11
                soft_total = player_t + 10 if player_t <= 11 else player_t
                if soft_total > BLACKJACK:
                    if player_t > d_total:
                        chunk_ev += 1
                    elif player_t < d_total:
                        chunk_ev -= 1
                else:
                    if soft_total > d_total:
                        chunk_ev += 1
                    elif soft_total < d_total:
                        chunk_ev -= 1
            else:
                if player_t > d_total:
                    chunk_ev += 1
                elif player_t < d_total:
                    chunk_ev -= 1
    return chunk_ev

def calculate_insurance_ev(shoe_counts):
    """
    Roughly: Insurance pays 2:1 if dealer has blackjack (hidden 10-value).
    The bet costs 1 for every 2 gain in success.
    EV = P(BJ)*2 - (1 - P(BJ))*1
    """
    total_cards = sum(shoe_counts.values())
    ten_value_cards = shoe_counts['T'] + shoe_counts['J'] + shoe_counts['Q'] + shoe_counts['K']
    if total_cards == 0:
        return 0
    prob_dealer_blackjack = ten_value_cards / total_cards
    insurance_ev = (prob_dealer_blackjack * 2) - (1 - prob_dealer_blackjack)
    return insurance_ev

def print_dealer_probabilities(shoe_counts, dealer_up):
    """
    Example usage if you want to show whether insurance is profitable.
    """
    if dealer_up == 'A':
        insurance_ev = calculate_insurance_ev(shoe_counts)
        if insurance_ev < 0:
            print("Insurance bet is unprofitable")
        else:
            print("Insurance bet is profitable")


###############################################################################
# NEW HELPER FOR PLAYING OUT A HAND (for Hit or after Split)
###############################################################################
def play_out_hand(player_hand, local_deck, allow_double=True, force_one_draw=False):
    """
    Plays out the player's hand based on simple logic:
      - If allow_double is True and we have exactly 2 cards with total <= 11,
        we draw exactly one card and stop (bet_multiplier=2).
      - Otherwise, we keep drawing if total < 17 (or until bust/shoe empty).
      - If force_one_draw=True, we ensure at least one draw if we are "Hitting," 
        even if the hand starts at 17+ (which can reflect a real 'Hit' choice).
    Returns:
      (player_hand, bet_multiplier)
    """
    bet_multiplier = 1
    drawn_once = False

    # 1) Handle Doubling logic if allowed & exactly 2 cards
    if allow_double and len(player_hand) == 2:
        current_total = hand_value(player_hand)
        # Example: Double if total <= 11
        if current_total <= 11 and len(local_deck) > 0:
            bet_multiplier = 2
            # Draw exactly 1 card
            drawn_card = random.choice(local_deck)
            local_deck.remove(drawn_card)
            player_hand.append(drawn_card)
            return player_hand, bet_multiplier

    # 2) Otherwise, keep hitting while total < 17
    #    but also optionally force a single draw if force_one_draw=True
    while True:
        current_total = hand_value(player_hand)

        # If we haven't drawn yet and force_one_draw is True, draw exactly once
        if force_one_draw and not drawn_once:
            if not local_deck:
                break
            new_card = random.choice(local_deck)
            local_deck.remove(new_card)
            player_hand.append(new_card)
            drawn_once = True

            # If bust, stop
            if hand_value(player_hand) > 21:
                break

            # After forcing the one draw, continue to next iteration
            continue

        # Now do standard "hit until 17+" logic
        if current_total >= 17:
            break
        if not local_deck:
            break

        new_card = random.choice(local_deck)
        local_deck.remove(new_card)
        player_hand.append(new_card)

        if hand_value(player_hand) > 21:
            break

    return player_hand, bet_multiplier

###############################################################################
# MONTE CARLO EV FUNCTION (UPDATED)
###############################################################################
def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """
    Main Monte Carlo function that calculates EV for one action:
    'Stand', 'Hit', 'Double Down', or 'Split'.

    Each simulation uses a fresh local shoe. 
    The final EV is scaled by RTP.
    """
    start_time = time.time()
    player_total = hand_value(player_cards)
    is_soft_player = is_soft_hand(player_cards)
    ev = 0
    checkpoint_means = []

    # We break simulations into 10 chunks to measure convergence
    chunk_size = simulations // 10

    # -------------------------------------------------------------------------
    # STAND
    # -------------------------------------------------------------------------
    if action == "Stand":
        for i in range(10):
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = process_results_for_stand_like(player_total, dealer_totals, is_soft_player)
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # HIT (with full "play_out_hand" logic)
    # -------------------------------------------------------------------------
    elif action == "Hit":
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                # Copy shoe and remove known cards
                local_shoe = build_shoe_list(shoe_counts)

                # Remove player's known cards
                tmp_cards = []
                for val in player_cards:
                    if val in local_shoe:
                        local_shoe.remove(val)
                    tmp_cards.append(val)

                # Remove the dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # Now fully play out the player's hand, forcing at least one draw
                # and disallowing double for a plain "Hit."
                tmp_cards, bet_factor = play_out_hand(
                    tmp_cards,
                    local_shoe,
                    allow_double=False,     # because we explicitly said "Hit"
                    force_one_draw=True     # ensures we draw at least one card
                )
                p_total = hand_value(tmp_cards)

                # Dealer finishes
                d_total = simulate_dealer_hand_once(dealer_card_val, local_shoe)

                # Compare
                if p_total > BLACKJACK:
                    ev_chunk -= 1
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 1
                    elif p_total < d_total:
                        ev_chunk -= 1

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # DOUBLE DOWN (only one extra card, no further hitting)
    # -------------------------------------------------------------------------
    elif action == "Double Down":
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                local_shoe = build_shoe_list(shoe_counts)

                # Remove player's known cards
                tmp_cards = []
                for val in player_cards:
                    if val in local_shoe:
                        local_shoe.remove(val)
                    tmp_cards.append(val)

                # Remove dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # Take exactly one draw
                draw_val = random.choice(local_shoe) if local_shoe else 0
                if draw_val in local_shoe:
                    local_shoe.remove(draw_val)
                tmp_cards.append(draw_val)

                p_total = hand_value(tmp_cards)

                # Dealer final
                d_total = simulate_dealer_hand_once(dealer_card_val, local_shoe)

                # Compare (double => +/- 2)
                if p_total > BLACKJACK:
                    ev_chunk -= 2
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 2
                    elif p_total < d_total:
                        ev_chunk -= 2

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    # -------------------------------------------------------------------------
    # SPLIT (DAS allowed)
    # -------------------------------------------------------------------------
    elif action == "Split":
        # The player's hand has exactly 2 cards of the same rank
        split_card_val = player_cards[0]
        split_ev_accumulator = 0

        # We have 2 sub-hands (since it's a split)
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                # Build a local shoe from the *global* shoe_counts,
                # which already has the player's & dealer's cards removed
                local_shoe = build_shoe_list(shoe_counts)

                # ─────────────────────────────────────────────────────────────
                # REMOVE (or comment out) the duplication below:
                #
                #   card_count = local_shoe.count(split_card_val)
                #   if card_count >= 2:
                #       local_shoe.remove(split_card_val)
                #       local_shoe.remove(split_card_val)
                #   else:
                #       # Not enough cards, skip iteration
                #       continue
                # ─────────────────────────────────────────────────────────────

                # Remove dealer upcard (because that's known to be in the dealer's hand)
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # --------- SUB-HAND #1 -----------
                # Start sub-hand with one copy of the split card
                sub_hand_1 = [split_card_val]
                # Draw one immediate card
                if local_shoe:
                    draw_val = random.choice(local_shoe)
                    local_shoe.remove(draw_val)
                    sub_hand_1.append(draw_val)

                # Now fully play out sub-hand #1 (DAS logic => allow_double=True)
                sub_hand_1, bet_mult_1 = play_out_hand(
                    sub_hand_1, 
                    local_shoe,
                    allow_double=True,   # Let them double if total <= 11
                    force_one_draw=False
                )
                p_total_1 = hand_value(sub_hand_1)

                # Dealer finishes
                d_total_1 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())

                # Resolve sub-hand #1
                if p_total_1 > BLACKJACK:
                    ev_sub_1 = -1 * bet_mult_1
                else:
                    if d_total_1 > BLACKJACK or p_total_1 > d_total_1:
                        ev_sub_1 = +1 * bet_mult_1
                    elif p_total_1 < d_total_1:
                        ev_sub_1 = -1 * bet_mult_1
                    else:
                        ev_sub_1 = 0

                # --------- SUB-HAND #2 -----------
                sub_hand_2 = [split_card_val]
                if local_shoe:
                    draw_val_2 = random.choice(local_shoe)
                    local_shoe.remove(draw_val_2)
                    sub_hand_2.append(draw_val_2)

                sub_hand_2, bet_mult_2 = play_out_hand(
                    sub_hand_2, 
                    local_shoe,
                    allow_double=True,
                    force_one_draw=False
                )
                p_total_2 = hand_value(sub_hand_2)

                d_total_2 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())

                if p_total_2 > BLACKJACK:
                    ev_sub_2 = -1 * bet_mult_2
                else:
                    if d_total_2 > BLACKJACK or p_total_2 > d_total_2:
                        ev_sub_2 = +1 * bet_mult_2
                    elif p_total_2 < d_total_2:
                        ev_sub_2 = -1 * bet_mult_2
                    else:
                        ev_sub_2 = 0

                # Combine results from both sub-hands
                ev_chunk += (ev_sub_1 + ev_sub_2)

            split_ev_accumulator += ev_chunk

        ev = split_ev_accumulator

    # -------------------------------------------------------------------------
    # FINAL EV SCALING
    # -------------------------------------------------------------------------
    elapsed_time = time.time() - start_time
    final_ev = (ev / simulations) * RTP

    # Print intermediate info
    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card_val}")
    print(f"Final EV for {action}: {final_ev:.5f}, Time: {elapsed_time:.2f}s")

    if checkpoint_means:
        benchmarks = " | ".join(
            [f"{(i + 1) * 10}%: {val:.5f}" for i, val in enumerate(checkpoint_means)]
        )
        print(f"Convergence: [{benchmarks}]")
    else:
        print("No convergence benchmarks available for this action.")

    return final_ev, elapsed_time, checkpoint_means


###############################################################################
# GET PLAYER ACTION (REMOVED 'not is_split_hand' TO ALLOW DAS)
###############################################################################
def get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn=True, is_split_hand=False):
    """
    Evaluate the EV of each possible action and pick the best one.
    """

    actions = ["Stand", "Hit"]

    # Double Down is now allowed if:
    # 1) It is the player's first turn
    # 2) They have exactly 2 cards
    # (We removed 'not is_split_hand' so it's effectively DAS)
    if is_first_turn and len(player_cards) == 2:
        actions.append("Double Down")

    # Only append "Split" if exactly 2 cards and same rank
    if is_first_turn and len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        actions.append("Split")
        
    evs = {}
    times = {}
    
    # Calculate EV for each possible action in 'actions'
    for action in actions:
        ev_val, elapsed_time, _ = monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action)
        evs[action] = ev_val
        times[action] = elapsed_time
        
    sorted_actions = sorted(evs.items(), key=lambda x: x[1], reverse=True)
    best_action = sorted_actions[0][0]
    second_best_action = sorted_actions[1][0] if len(sorted_actions) > 1 else None
    ev_diff = sorted_actions[0][1] - sorted_actions[1][1] if len(sorted_actions) > 1 else 0
    
    print("\nPlayer Cards (numeric):", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card (value):", dealer_card_val)
    print("Expected Values (EVs):")
    
    for action, evval in evs.items():
        if action == best_action:
            color_str = Fore.GREEN
        elif action == second_best_action:
            color_str = Fore.LIGHTYELLOW_EX + Style.DIM
        else:
            color_str = Fore.RED + Style.DIM
        
        reset_str = Style.RESET_ALL
        print(f" {color_str}{action}: {evval:.5f} ({times[action]:.2f}s){reset_str}")
        
        if action == best_action and second_best_action:
            print(f"  /EVdiff: {Fore.CYAN}{ev_diff:.5f}{Style.RESET_ALL} vs {second_best_action}")
            
    print(f"\nOptimal Action: {Fore.GREEN}{best_action}{Style.RESET_ALL} ({times[best_action]:.2f} seconds)\n")
    return best_action


###############################################################################
# MAIN
###############################################################################
def main():
    global running_count
    print("Blackjack Optimal Strategy Solver (No NumPy) with a Persistent Shoe State\n")
    print("(Type '0' in the dealer/player/removal prompts to reset the shoe and start a new sequence)\n")
    
    shoe_counts = initialize_shoe_counts(NUM_DECKS)
    running_count = 0
    
    while True:
        backup_shoe_counts = shoe_counts.copy()
        try:
            total_cards = 52 * NUM_DECKS
            current_remaining = sum(shoe_counts.values())
            played = total_cards - current_remaining
            played_pct = (played / total_cards) * 100
            remain_pct = 100 - played_pct
            divisor = current_remaining / 52.0  # decks left
            true_count = running_count / divisor if divisor > 0 else 0
            
            print(f"{played} / {total_cards} ({played_pct:.2f}%) played | "
                  f"{current_remaining} / {total_cards} ({remain_pct:.2f}%) remaining | "
                  f"Running Count: {running_count:.1f} | "
                  f"Divisor: {divisor:.1f} | "
                  f"True Count: {true_count:.1f}")
            
            dealer_card_input = input("Enter Dealer's visible card (2-9 or T/J/Q/K/A) or 0 to reset: ").strip().upper()
            if dealer_card_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                running_count = 0
                print("\nShoe has been reset! Starting a new hand...\n")
                continue
            if len(dealer_card_input) != 1 or dealer_card_input not in ALL_RANKS:
                raise ValueError("Invalid dealer card input!")
            remove_card_from_shoe(shoe_counts, dealer_card_input)
            dealer_card_val = RANK_TO_VALUE[dealer_card_input]
            
            # Check insurance if dealer upcard is Ace
            if dealer_card_input == 'A':
                insurance_ev = calculate_insurance_ev(shoe_counts)
                if insurance_ev > 0:
                    print(f"\nInsurance EV: {Fore.GREEN + Style.BRIGHT}{insurance_ev:.5f}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN + Style.DIM}Insurance bet is profitable{Style.RESET_ALL}")
                else:
                    print(f"\nInsurance EV: {Fore.RED + Style.BRIGHT}{insurance_ev:.5f}{Style.RESET_ALL}")
                    print(f"{Fore.RED + Style.DIM}Insurance bet is unprofitable{Style.RESET_ALL}")

            player_input = input("Enter Player's cards (2 chars, e.g. 'T5', 'J9', '77') or 0 to reset: ").strip().upper()
            if player_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                running_count = 0
                print("\nShoe has been reset! Starting a new hand...\n")
                continue
            if len(player_input) != 2:
                raise ValueError("You must enter exactly two characters for the player's hand (e.g. 'T5').")
            
            player_cards = []
            for c in player_input:
                if c not in ALL_RANKS:
                    raise ValueError(f"Invalid player card '{c}'!")
                remove_card_from_shoe(shoe_counts, c)
                player_cards.append(RANK_TO_VALUE[c])
            
            pre_calc_removal = input("Enter cards to remove before calculations (e.g. 'T5') or 0 for none/reset: ").strip().upper()
            if pre_calc_removal == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                running_count = 0
                print("\nShoe has been reset! Starting a new hand...\n")
                continue
            if pre_calc_removal:
                for c in pre_calc_removal:
                    if c not in ALL_RANKS:
                        raise ValueError(f"Invalid removal card '{c}'!")
                    remove_card_from_shoe(shoe_counts, c)

            # Set flags for new hand
            is_split_hand = False
            first_turn = True

            # Player decision loop
            while True:
                best_action = get_player_action(
                    player_cards,
                    dealer_card_val,
                    shoe_counts,
                    is_first_turn=first_turn,
                    is_split_hand=is_split_hand
                )
                
                # After the first decision, no more double-down is offered
                first_turn = False

                if best_action == "Hit":
                    hit_card = input("Enter the hit card (2-9 or T/J/Q/K/A) or press Enter to stop hitting: ").strip().upper()
                    if not hit_card:
                        # Player decides to stop hitting
                        break
                    if hit_card not in ALL_RANKS:
                        raise ValueError(f"Invalid hit card '{hit_card}'!")
                    remove_card_from_shoe(shoe_counts, hit_card)
                    player_cards.append(RANK_TO_VALUE[hit_card])
                    
                    if hand_value(player_cards) >= 21:
                        break

                elif best_action == "Split":
                    # If you allow double after a split, keep is_split_hand=True
                    is_split_hand = True
                    # For demonstration, we won't fully resolve the real-time dealing
                    # of sub-hands here. The simulation from monte_carlo_ev() has already
                    # told us the best strategy. We'll just break the loop.
                    break

                else:
                    # "Stand" or "Double Down" => we break out
                    break
            
            final_removal_input = input("Enter final cards to remove (e.g. 'T5') or 0 for none/resets: ").strip().upper()
            if final_removal_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                running_count = 0
                print("\nShoe has been reset! Starting a new hand...\n")
                continue
            if final_removal_input:
                for c in final_removal_input:
                    if c not in ALL_RANKS:
                        raise ValueError(f"Invalid removal card '{c}'!")
                    remove_card_from_shoe(shoe_counts, c)
                    
            print_shoe_status(shoe_counts, NUM_DECKS)
            print("Starting next hand...\n")
            
        except ValueError as e:
            shoe_counts = backup_shoe_counts
            print(f"Invalid input: {e}")
            print("Please try again.\n")
            continue


if __name__ == "__main__":
    main()
