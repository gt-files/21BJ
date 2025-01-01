import random
from colorama import Fore, Style, init
import time

# Initialize colorama
init()

# Constants
BLACKJACK = 21          
DEALER_STAND = 17       
NUM_DECKS = 6           
SIMULATIONS = 25000     
RTP = 0.995             
MAX_DIFF = 0.00999      # Maximum EV difference threshold for user choice

ACTION_SHORTCUTS = {
    'H': 'Hit',
    'S': 'Stand',
    'DD': 'Double Down',
    'SP': 'Split'
}


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
    global running_count
    if shoe_counts[rank] > 0:
        shoe_counts[rank] -= 1
        running_count += COUNTING_SYSTEM[rank]
    else:
        raise ValueError(f"Card '{rank}' not found (count is 0).")

def build_shoe_list(shoe_counts):
    cards_list = []
    for rank in ALL_RANKS:
        count = shoe_counts[rank]
        val = RANK_TO_VALUE[rank]
        if count > 0:
            cards_list.extend([val] * count)
    return cards_list

def hand_value(cards):
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hands(dealer_card_val, shoe_counts, num_simulations):
    shoe_list = build_shoe_list(shoe_counts)
    final_totals = [0] * num_simulations
    
    for i in range(num_simulations):
        dealer_cards = [dealer_card_val]
        while True:
            total = hand_value(dealer_cards)
            if total < DEALER_STAND:
                if not shoe_list:
                    break
                draw_val = random.choice(shoe_list)
                dealer_cards.append(draw_val)
            else:
                final_totals[i] = total
                break
                
    return final_totals

def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    player_total = hand_value(player_cards)
    ev = 0
    checkpoint_means = []
    
    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card_val}")
    start_time = time.time()
    chunk_size = simulations // 10
    
    def process_results_for_stand_like(player_t, dealer_totals_list, multiplier=1):
        if player_t > BLACKJACK:
            return -multiplier * len(dealer_totals_list)
        
        chunk_ev = 0
        for d_total in dealer_totals_list:
            if d_total > BLACKJACK:
                chunk_ev += multiplier
            else:
                if player_t > d_total:
                    chunk_ev += multiplier
                elif player_t < d_total:
                    chunk_ev -= multiplier
        return chunk_ev

    if action == "Stand":
        for i in range(10):
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = process_results_for_stand_like(player_total, dealer_totals, multiplier=1)
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))
            
    elif action == "Hit":
        for i in range(10):
            shoe_list = build_shoe_list(shoe_counts)
            if not shoe_list:
                break
                
            new_totals = []
            for _ in range(chunk_size):
                draw_val = random.choice(shoe_list)
                new_totals.append(player_total + draw_val)
                
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = 0
            
            for p_t, d_t in zip(new_totals, dealer_totals):
                if p_t > BLACKJACK:
                    ev_chunk -= 1
                else:
                    if d_t > BLACKJACK or p_t > d_t:
                        ev_chunk += 1
                    elif p_t < d_t:
                        ev_chunk -= 1
                        
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))
            
    elif action == "Double Down":
        for i in range(10):
            shoe_list = build_shoe_list(shoe_counts)
            if not shoe_list:
                break
                
            new_totals = []
            for _ in range(chunk_size):
                draw_val = random.choice(shoe_list)
                new_totals.append(player_total + draw_val)
                
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = 0
            
            for p_t, d_t in zip(new_totals, dealer_totals):
                if p_t > BLACKJACK:
                    ev_chunk -= 2
                else:
                    if d_t > BLACKJACK or p_t > d_t:
                        ev_chunk += 2
                    elif p_t < d_t:
                        ev_chunk -= 2
                        
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))
            
    elif action == "Split":
        split_ev_accumulator = 0
        split_card_val = player_cards[0]
        
        for split_index in range(2):
            hand_ev = 0
            for i in range(10):
                shoe_list = build_shoe_list(shoe_counts)
                if not shoe_list:
                    break
                    
                new_totals = []
                for _ in range(chunk_size):
                    draw_val = random.choice(shoe_list)
                    new_totals.append(split_card_val + draw_val)
                    
                dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
                ev_chunk = 0
                
                for p_t, d_t in zip(new_totals, dealer_totals):
                    if p_t > BLACKJACK:
                        ev_chunk -= 1
                    else:
                        if d_t > BLACKJACK or p_t > d_t:
                            ev_chunk += 1
                        elif p_t < d_t:
                            ev_chunk -= 1
                            
                hand_ev += ev_chunk
                if split_index == 0:
                    checkpoint_means.append(hand_ev / ((i + 1) * chunk_size))
                    
            split_ev_accumulator += hand_ev
            
        ev = split_ev_accumulator / 2

    elapsed_time = time.time() - start_time
    final_ev = (ev / simulations) * RTP
    
    print(f"Final EV for {action}: {final_ev:.5f}, Time: {elapsed_time:.2f}s")
    
    if checkpoint_means:
        benchmarks = " | ".join([f"{(i + 1) * 10}%: {val:.5f}" for i, val in enumerate(checkpoint_means)])
        print(f"Convergence: [{benchmarks}]")
    else:
        print("No convergence benchmarks available for this action.")
        
    return final_ev, elapsed_time, checkpoint_means

def get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn=True):
    actions = ["Stand", "Hit"]
    
    # Only add Double Down if it's the first turn
    if is_first_turn:
        actions.append("Double Down")
    
    # Split is still available if we have a pair, regardless of turn
    if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
        actions.append("Split")
    
    evs = {}
    times = {}
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
    
    # Print all actions except the best one first
    for action, evval in evs.items():
        if action != best_action:
            color_str = Fore.LIGHTYELLOW_EX + Style.DIM if action == second_best_action else Fore.RED + Style.DIM
            reset_str = Style.RESET_ALL
            print(f" {color_str}{action}: {evval:.5f} ({times[action]:.2f}s){reset_str}")

    # Print the best action and EVdiff immediately after
    print(f" {Fore.GREEN}{best_action}: {evs[best_action]:.5f} ({times[best_action]:.2f}s){Style.RESET_ALL}")
    if second_best_action:
        print(f" /EVdiff: {Fore.CYAN}{ev_diff:.5f}{Style.RESET_ALL} vs {second_best_action}")

    if abs(ev_diff) < MAX_DIFF and second_best_action:
        print(f"\nThe difference between {best_action} and {second_best_action} is small.")
        print("Use: H for Hit, S for Stand, DD for Double Down, SP for Split")
        while True:
            choice = input(f"Would you like to {best_action} or {second_best_action}? ").strip().upper()
            if choice in ACTION_SHORTCUTS and ACTION_SHORTCUTS[choice] in [best_action, second_best_action]:
                final_choice = ACTION_SHORTCUTS[choice]
                print(f"\nYou chose: {Fore.GREEN}{final_choice}{Style.RESET_ALL}")
                return final_choice
            print(f"Please enter either a shortcut for '{best_action}' or '{second_best_action}'")
    else:
        print(f"\nOptimal Action: {Fore.GREEN}{best_action}{Style.RESET_ALL} ({times[best_action]:.2f} seconds)\n")
        return best_action
    
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
            divisor = current_remaining / 52  # Calculate number of remaining decks
            true_count = running_count / divisor if divisor > 0 else 0  # Calculate true count
            
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
                
            if len(dealer_card_input) != 1:
                raise ValueError("Dealer input must be exactly 1 character!")
            if dealer_card_input not in ALL_RANKS:
                raise ValueError("Invalid dealer card input!")
                
            remove_card_from_shoe(shoe_counts, dealer_card_input)
            dealer_card_val = RANK_TO_VALUE[dealer_card_input]
            
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
            
            # Modified hit loop with first turn tracking
            is_first_turn = True
            while True:
                best_action = get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn)
                if best_action == "Hit":
                    hit_card = input("Enter the hit card (2-9 or T/J/Q/K/A) or press Enter to stop hitting: ").strip().upper()
                    if not hit_card:
                        break
                    if hit_card not in ALL_RANKS:
                        raise ValueError(f"Invalid hit card '{hit_card}'!")
                    remove_card_from_shoe(shoe_counts, hit_card)
                    player_cards.append(RANK_TO_VALUE[hit_card])
                    is_first_turn = False  # Set to False after first hit
                    if hand_value(player_cards) >= 21:
                        break
                else:
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