import random
from colorama import Fore, Style, init
import time

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 6
SIMULATIONS = 10000000  # <= You can reduce this for testing
RTP = 0.995

ALL_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

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
    '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 10, 'Q': 10, 'K': 10,
    'A': 11
}

def initialize_shoe_counts(num_decks):
    """Returns a dict { rank: count } for each rank, with 4 * num_decks copies each."""
    shoe_counts = {}
    for rank in ALL_RANKS:
        shoe_counts[rank] = 4 * num_decks
    return shoe_counts

def print_shoe_status(shoe_counts, num_decks):
    """Print how many copies of each card remain in the shoe, descending order (A down to 2)."""
    print("\nCurrent Shoe Status:")
    for rank in reversed(ALL_RANKS):
        max_copies = 4 * num_decks
        current = shoe_counts[rank]
        rank_name = RANK_TO_NAME[rank]
        print(f"  {rank_name}: {current} of {max_copies}")
    print("")

def remove_card_from_shoe(shoe_counts, rank):
    """
    Decrements the count for 'rank' in shoe_counts by 1, if available,
    otherwise raises ValueError.
    """
    if shoe_counts[rank] > 0:
        shoe_counts[rank] -= 1
    else:
        raise ValueError(f"Card '{rank}' not found (count is 0).")

def build_shoe_list(shoe_counts):
    """
    Converts shoe_counts into a simple list of card values from RANK_TO_VALUE.
    For example, if shoe_counts = {'A': 2, 'K': 4}, we return a list
    with 2 copies of 11, 4 copies of 10, etc.
    This list is used for random draws *with replacement* in each simulation step.
    """
    cards_list = []
    for rank in ALL_RANKS:
        count = shoe_counts[rank]
        val = RANK_TO_VALUE[rank]
        if count > 0:
            cards_list.extend([val] * count)
    return cards_list

def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hands(dealer_card_val, shoe_counts, num_simulations):
    """
    Simulate the dealer's final totals for 'num_simulations' rounds,
    each time starting from 'dealer_card_val' and hitting until >= DEALER_STAND or bust.
    Dynamically updates shoe_counts during simulation.
    """
    final_totals = []

    for _ in range(num_simulations):
        dealer_cards = [dealer_card_val]
        while True:
            total = hand_value(dealer_cards)
            if total < DEALER_STAND:
                available_cards = [rank for rank, count in shoe_counts.items() if count > 0]
                if not available_cards:
                    break

                draw_rank = random.choice(available_cards)
                dealer_cards.append(RANK_TO_VALUE[draw_rank])
                shoe_counts[draw_rank] -= 1

            else:
                final_totals.append(total)
                break

    return final_totals

def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """
    Estimate the EV for a given action using Monte Carlo simulations.
    'player_cards' = list of integer values for player's initial cards
    'dealer_card_val' = integer value for dealer's visible card
    'shoe_counts' = current shoe state
    'action' = 'Stand', 'Hit', 'Double Down', or 'Split'
    'simulations' = how many total simulations to run
    """
    start_time = time.time()
    player_total = hand_value(player_cards)
    ev = 0

    def process_results_for_stand_like(player_t, dealer_totals_list, multiplier=1):
        """For standard stand/hit/double logic."""
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
        dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts.copy(), simulations)
        ev = process_results_for_stand_like(player_total, dealer_totals, multiplier=1)

    elif action == "Hit":
        for _ in range(simulations):
            available_cards = [rank for rank, count in shoe_counts.items() if count > 0]
            if not available_cards:
                break

            draw_rank = random.choice(available_cards)
            shoe_counts[draw_rank] -= 1
            new_total = hand_value(player_cards + [RANK_TO_VALUE[draw_rank]])

            if new_total > BLACKJACK:
                ev -= 1
            else:
                dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts.copy(), 1)
                ev += process_results_for_stand_like(new_total, dealer_totals, multiplier=1)

    elif action == "Double Down":
        for _ in range(simulations):
            available_cards = [rank for rank, count in shoe_counts.items() if count > 0]
            if not available_cards:
                break

            draw_rank = random.choice(available_cards)
            shoe_counts[draw_rank] -= 1
            new_total = hand_value(player_cards + [RANK_TO_VALUE[draw_rank]])

            if new_total > BLACKJACK:
                ev -= 2
            else:
                dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts.copy(), 1)
                ev += process_results_for_stand_like(new_total, dealer_totals, multiplier=2)

    elif action == "Split":
        split_ev_accumulator = 0
        split_card_val = player_cards[0]

        for _ in range(simulations):
            for _ in range(2):
                available_cards = [rank for rank, count in shoe_counts.items() if count > 0]
                if not available_cards:
                    break

                draw_rank = random.choice(available_cards)
                shoe_counts[draw_rank] -= 1
                new_total = hand_value([split_card_val, RANK_TO_VALUE[draw_rank]])

                if new_total > BLACKJACK:
                    split_ev_accumulator -= 1
                else:
                    dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts.copy(), 1)
                    split_ev_accumulator += process_results_for_stand_like(new_total, dealer_totals, multiplier=1)

        ev = split_ev_accumulator / 2

    final_ev = (ev / simulations) * RTP
    elapsed_time = time.time() - start_time
    return final_ev, elapsed_time, None

def get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn=True):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit"]
    if is_first_turn:
        actions.append("Double Down")
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
    for action, evval in evs.items():
        color_str = Fore.GREEN if action == best_action else ""
        reset_str = Style.RESET_ALL if action == best_action else ""
        print(f"  {color_str}{action}: {evval:.5f} ({times[action]:.2f}s){reset_str}")
        if action == best_action and second_best_action is not None:
            print(f"    EVdiff: {Fore.MAGENTA}{ev_diff:.5f}{Style.RESET_ALL} vs {second_best_action}")

    print(f"\nOptimal Action: {best_action} ({times[best_action]:.2f} seconds)\n")
    return best_action

def main():
    print("Blackjack Optimal Strategy Solver (No NumPy) with a Persistent Shoe State\n")
    print("(Type '0' in the dealer/player/removal prompts to reset the shoe and start a new sequence)\n")

    shoe_counts = initialize_shoe_counts(NUM_DECKS)

    while True:
        backup_shoe_counts = shoe_counts.copy()

        try:
            total_cards = 52 * NUM_DECKS
            current_remaining = sum(shoe_counts.values())
            played = total_cards - current_remaining
            played_pct = (played / total_cards) * 100
            remain_pct = 100 - played_pct
            print(f"{played} / {total_cards} ({played_pct:.2f}%) played | "
                  f"{current_remaining} / {total_cards} ({remain_pct:.2f}%) remaining")

            dealer_card_input = input(
                "Enter Dealer's visible card (2-9 or T/J/Q/K/A) or 0 to reset: "
            ).strip().upper()

            if dealer_card_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                print("\nShoe has been reset! Starting a new hand...\n")
                continue

            if len(dealer_card_input) != 1:
                raise ValueError("Dealer input must be exactly 1 character!")
            if dealer_card_input not in ALL_RANKS:
                raise ValueError("Invalid dealer card input!")
            remove_card_from_shoe(shoe_counts, dealer_card_input)
            dealer_card_val = RANK_TO_VALUE[dealer_card_input]

            player_input = input(
                "Enter Player's cards (2 chars, e.g. 'T5', 'J9', '77') or 0 to reset: "
            ).strip().upper()

            if player_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                print("\nShoe has been reset! Starting a new hand...\n")
                continue

            if len(player_input) != 2:
                raise ValueError(
                    "You must enter exactly two characters for the player's hand (e.g. 'T5')."
                )

            player_cards = []
            for c in player_input:
                if c not in ALL_RANKS:
                    raise ValueError(f"Invalid player card '{c}'!")
                remove_card_from_shoe(shoe_counts, c)
                player_cards.append(RANK_TO_VALUE[c])

            removal_input = input(
                "Enter cards to remove (e.g. 'T5') or 0 for none/resets: "
            ).strip().upper()

            if removal_input == '0':
                if len(removal_input) == 1:
                    shoe_counts = initialize_shoe_counts(NUM_DECKS)
                    print("\nShoe has been reset! Starting a new hand...\n")
                    continue

            elif removal_input != "":
                for c in removal_input:
                    if c not in ALL_RANKS:
                        raise ValueError(f"Invalid removal card '{c}'!")
                    remove_card_from_shoe(shoe_counts, c)

            while True:
                best_action = get_player_action(
                    player_cards,
                    dealer_card_val,
                    shoe_counts,
                    is_first_turn=(len(player_cards) == 2)
                )

                if best_action == "Stand":
                    print("You chose to stand. Ending turn.\n")
                    break

                if best_action == "Hit":
                    new_card_input = input(
                        "Enter the next drawn card (2-9 or T/J/Q/K/A): "
                    ).strip().upper()

                    if len(new_card_input) != 1:
                        raise ValueError("Drawn card must be exactly 1 character!")
                    if new_card_input not in ALL_RANKS:
                        raise ValueError(f"Invalid drawn card '{new_card_input}'!")

                    remove_card_from_shoe(shoe_counts, new_card_input)
                    player_cards.append(RANK_TO_VALUE[new_card_input])

                    if hand_value(player_cards) > BLACKJACK:
                        print(f"Player busted with {hand_value(player_cards)}!\n")
                        break

                elif best_action == "Double Down":
                    print("You chose to Double Down. (No extra card drawn.) Ending turn.\n")
                    break

                elif best_action == "Split":
                    print("\nYou chose to split!")
                    ev_split, _, _ = monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, "Split")
                    print(f"EV for split: {ev_split:.5f}\n")
                    break

            print_shoe_status(shoe_counts, NUM_DECKS)
            print("Starting next hand...\n")

        except ValueError as e:
            shoe_counts = backup_shoe_counts
            print(f"Invalid input: {e}")
            print("Please try again.\n")
            continue

if __name__ == "__main__":
    main()
