import random
from colorama import Fore, Style, init
import time

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 6
SIMULATIONS = 10000
RTP = 0.995

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
    '2': 1.0, '7': 1.0, '3': 1.0, '6': 2.0, '4': 2.0, '5': 2.0,
    '8': 0.0, '9': -1.0, 'T': -2.0, 'J': -2.0, 'Q': -2.0, 'K': -2.0, 'A': 0.0
}

# Global running count
running_count = 0

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
    Returns the best total under/equals 21 if possible.
    Aces are valued 11 or 1.
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
    # After adjusting for 'soft' aces, if any aces are left, it's soft.
    return aces > 0

def simulate_dealer_hand_once(dealer_card_val, shoe_list):
    """
    Simulate a single dealer hand starting with dealer_card_val,
    drawing from a *local copy* of shoe_list (so each simulation
    is independent). Returns the dealer's final total.
    """
    local_shoe = shoe_list.copy()
    # Remove the known dealer upcard from the local shoe once
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

def play_out_hand(cards, local_shoe):
    """
    Keep hitting this player's hand according to your logic or standard strategy,
    until they stand or bust.
    """
    # Example: keep hitting until total >= 17, or total is a soft 18, etc.
    # In real code, you'd do something more refined than this
    while True:
        t = hand_value(cards)
        if t >= 17:  # or use your custom logic
            break
        if not local_shoe:
            break
        new_card = random.choice(local_shoe)
        local_shoe.remove(new_card)
        cards.append(new_card)
        if hand_value(cards) > 21:
            break
    return cards

def compare_final_totals(player_total, dealer_total):
    """
    Return +1 if player wins, -1 if dealer wins, 0 if push.
    """
    if player_total > 21:
        return -1
    elif dealer_total > 21:
        return +1
    elif player_total > dealer_total:
        return +1
    elif player_total < dealer_total:
        return -1
    else:
        return 0


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
    Utility to compare a standing player's total vs. many dealer totals.
    Returns the sum of +1 win / -1 loss for the entire list.
    """
    if player_t > BLACKJACK:
        return -1 * len(dealer_totals_list)
    
    chunk_ev = 0
    for d_total in dealer_totals_list:
        if d_total > BLACKJACK:
            chunk_ev += 1
        else:
            # Soft hand: check whether using Ace as 1 or 11 is better
            if is_soft:
                soft_total = player_t + 10 if player_t <= 11 else player_t
                if max(soft_total, player_t) > d_total:
                    chunk_ev += 1
                elif max(soft_total, player_t) < d_total:
                    chunk_ev -= 1
            else:
                if player_t > d_total:
                    chunk_ev += 1
                elif player_t < d_total:
                    chunk_ev -= 1
    return chunk_ev

def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """
    Main Monte Carlo function that calculates EV for one action:
    'Stand', 'Hit', 'Double Down', or 'Split'.

    Each simulation should sample from the shoe independently.
    The final EV is scaled by RTP.
    """
    import time
    start_time = time.time()
    player_total = hand_value(player_cards)
    is_soft_player = is_soft_hand(player_cards)
    ev = 0
    checkpoint_means = []

    # We break simulations into 10 chunks to measure convergence
    chunk_size = simulations // 10

    # Helper function for fully playing out a "Hit" hand:
    def play_out_hand(p_cards, local_deck):
        """
        Keep drawing until total >= 17 (or bust) -- a simple placeholder logic.
        You can replace with any more detailed strategy (e.g. basic strategy).
        """
        while True:
            total_now = hand_value(p_cards)
            if total_now >= 17:      # Stop hitting at 17+
                break
            if not local_deck:      # No cards left to draw
                break
            # Draw one card
            new_card_val = random.choice(local_deck)
            local_deck.remove(new_card_val)
            p_cards.append(new_card_val)
            # Stop if bust
            if hand_value(p_cards) > 21:
                break
        return p_cards

    ############################################################################
    # STAND
    ############################################################################
    if action == "Stand":
        # 10 chunks to measure EV over time
        for i in range(10):
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = process_results_for_stand_like(player_total, dealer_totals, is_soft_player)
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    ############################################################################
    # HIT
    ############################################################################
    elif action == "Hit":
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                # Copy shoe and remove known cards
                local_shoe = build_shoe_list(shoe_counts)

                # Remove the existing player cards
                tmp_cards = []
                for val in player_cards:
                    if val in local_shoe:
                        local_shoe.remove(val)
                    tmp_cards.append(val)

                # Remove the dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # Now fully play out the player's hand
                tmp_cards = play_out_hand(tmp_cards, local_shoe)

                # Evaluate player's final total
                p_total = hand_value(tmp_cards)

                # Dealer finishes
                d_total = simulate_dealer_hand_once(dealer_card_val, local_shoe)

                # Compare results
                if p_total > BLACKJACK:
                    ev_chunk -= 1
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 1
                    elif p_total < d_total:
                        ev_chunk -= 1

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    ############################################################################
    # DOUBLE DOWN
    ############################################################################
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

                # Compare (double down => +/- 2)
                if p_total > BLACKJACK:
                    ev_chunk -= 2
                else:
                    if d_total > BLACKJACK or p_total > d_total:
                        ev_chunk += 2
                    elif p_total < d_total:
                        ev_chunk -= 2

            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    ############################################################################
    # SPLIT
    ############################################################################
    elif action == "Split":
        split_card_val = player_cards[0]
        split_ev_accumulator = 0

        # We'll do N simulations and sum up the result of both sub-hands each time
        # (since each split is effectively two independent 1-unit bets).
        for i in range(10):
            ev_chunk = 0
            for _ in range(chunk_size):
                local_shoe = build_shoe_list(shoe_counts)
                
                # Remove both original cards
                if local_shoe.count(split_card_val) >= 2:
                    local_shoe.remove(split_card_val)
                    local_shoe.remove(split_card_val)
                else:
                    continue  # or handle error

                # Remove dealer upcard
                if dealer_card_val in local_shoe:
                    local_shoe.remove(dealer_card_val)

                # ----- SUB-HAND 1 -----
                sub_hand_1 = [split_card_val]
                new_card_1 = random.choice(local_shoe)
                local_shoe.remove(new_card_1)
                sub_hand_1.append(new_card_1)

                # keep hitting sub_hand_1 if needed (depending on your strategy)
                sub_hand_1 = play_out_hand(sub_hand_1, local_shoe)  
                p_total_1 = hand_value(sub_hand_1)

                # dealer’s final for sub-hand #1
                dealer_final_1 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())

                # Evaluate sub-hand #1
                result_1 = compare_final_totals(p_total_1, dealer_final_1)

                # ----- SUB-HAND 2 -----
                # We start again with the same split_card_val
                sub_hand_2 = [split_card_val]
                new_card_2 = random.choice(local_shoe)
                local_shoe.remove(new_card_2)
                sub_hand_2.append(new_card_2)

                # keep hitting sub_hand_2
                sub_hand_2 = play_out_hand(sub_hand_2, local_shoe)
                p_total_2 = hand_value(sub_hand_2)

                dealer_final_2 = simulate_dealer_hand_once(dealer_card_val, local_shoe.copy())
                result_2 = compare_final_totals(p_total_2, dealer_final_2)

                # Each sub-hand is +1 / -1 / 0 (push).
                # Summation of both sub-hands
                ev_chunk += (result_1 + result_2)

            split_ev_accumulator += ev_chunk

        ev = split_ev_accumulator / (10 * chunk_size)


    # Scale final EV by RTP
    elapsed_time = time.time() - start_time
    final_ev = (ev / simulations) * RTP

    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card_val}")
    print(f"Final EV for {action}: {final_ev:.5f}, Time: {elapsed_time:.2f}s")

    if checkpoint_means:
        benchmarks = " | ".join([f"{(i + 1) * 10}%: {val:.5f}"
                                 for i, val in enumerate(checkpoint_means)])
        print(f"Convergence: [{benchmarks}]")
    else:
        print("No convergence benchmarks available for this action.")

    return final_ev, elapsed_time, checkpoint_means

def get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn=True, is_split_hand=False):
    """
    Evaluate the EV of each possible action and pick the best one.
    """

    actions = ["Stand", "Hit"]

    # Only allow Double Down if:
    #   1) It is the player's first turn of the hand
    #   2) They have exactly 2 cards
    #   3) It is not a split hand (if you want to forbid double after split)
    ### CHANGED LINES BELOW ###
    if is_first_turn and len(player_cards) == 2 and not is_split_hand:
        actions.append("Double Down")
    ### CHANGED LINES ABOVE ###

    # Only append "Split" if exactly 2 cards and same rank
    # (still requires it to be the first turn in standard Blackjack)
    if is_first_turn and len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        actions.append("Split")
        
    evs = {}
    times = {}
    
    # Calculate EV for each possible action in 'actions'
    for action in actions:
        ev, elapsed_time, _ = monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action)
        evs[action] = ev
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
            
            # Insurance check if upcard is Ace
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
                    is_split_hand=is_split_hand  # Let the get_player_action check if it's split
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
                    # If you want to forbid double after a split, keep is_split_hand=True
                    # If you allow double after a split (DAS), set is_split_hand=False
                    is_split_hand = True
                    # Handle your split logic here; for now, we just break:
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
