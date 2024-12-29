import random
from colorama import Fore, Style, init
import time
import numpy as np

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 6
SIMULATIONS = 100000000
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
    '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9,
    'T': 10, 'J': 10, 'Q': 10, 'K': 10,
    'A': 11
}

rng = np.random.default_rng(np.random.PCG64())

def initialize_shoe_counts(num_decks):
    """Returns a dict { rank: count } for each rank in ALL_RANKS, with 4 * num_decks copies each."""
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

def build_numeric_shoe_array(shoe_counts):
    """
    Converts shoe_counts into a numeric array suitable for rng.choice.
    e.g., if shoe_counts = {'A': 2, 'K': 4, ...}, we produce an array
    with 2 copies of 11 (Ace), 4 copies of 10 (King), etc.
    """
    cards_list = []
    for rank in ALL_RANKS:
        count = shoe_counts[rank]
        val = RANK_TO_VALUE[rank]
        if count > 0:
            cards_list.extend([val] * count)
    return np.array(cards_list, dtype=int)

def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand_vectorized(dealer_card_val, shoe_counts, num_simulations):
    """Vectorized simulation of dealer hands using the numeric shoe array."""
    shoe_array = build_numeric_shoe_array(shoe_counts)

    dealer_hands = np.full(num_simulations, dealer_card_val)
    dealer_totals = np.full(num_simulations, hand_value([dealer_card_val]))

    while True:
        hits = dealer_totals < DEALER_STAND
        if not np.any(hits):
            break

        new_cards = rng.choice(shoe_array, size=num_simulations)
        dealer_hands = np.where(hits, dealer_hands + new_cards, dealer_hands)
        dealer_totals = np.where(hits, dealer_totals + new_cards, dealer_totals)

        # Adjust for aces if total > 21
        hits_aces = (dealer_totals > BLACKJACK) & (dealer_hands == 11)
        dealer_totals = np.where(hits_aces, dealer_totals - 10, dealer_totals)

    return dealer_totals

def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """Estimate the EV for a given action using Monte Carlo simulations."""
    player_total = hand_value(player_cards)
    ev = 0
    checkpoint_means = []

    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card_val}")

    start_time = time.time()
    chunk_size = simulations // 10

    if action == "Stand":
        for i in range(10):
            dealer_totals = simulate_dealer_hand_vectorized(dealer_card_val, shoe_counts, chunk_size)
            ev += np.sum((dealer_totals > BLACKJACK) | (player_total > dealer_totals))
            ev -= np.sum(player_total < dealer_totals)
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Hit":
        for i in range(10):
            shoe_array = build_numeric_shoe_array(shoe_counts)
            new_cards = rng.choice(shoe_array, size=chunk_size)
            new_totals = player_total + new_cards

            dealer_totals = simulate_dealer_hand_vectorized(dealer_card_val, shoe_counts, chunk_size)

            win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
            lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
            bust_conditions = (new_totals > BLACKJACK)

            ev += np.sum(win_conditions)
            ev -= np.sum(lose_conditions)
            ev -= np.sum(bust_conditions)
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Double Down":
        for i in range(10):
            shoe_array = build_numeric_shoe_array(shoe_counts)
            new_cards = rng.choice(shoe_array, size=chunk_size)
            new_totals = player_total + new_cards

            dealer_totals = simulate_dealer_hand_vectorized(dealer_card_val, shoe_counts, chunk_size)

            win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
            lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
            bust_conditions = (new_totals > BLACKJACK)

            ev += 2 * np.sum(win_conditions)
            ev -= 2 * np.sum(lose_conditions)
            ev -= 2 * np.sum(bust_conditions)
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Split":
        split_ev = 0
        for _ in range(2):
            for i in range(10):
                shoe_array = build_numeric_shoe_array(shoe_counts)
                split_card_val = player_cards[0]
                new_cards = rng.choice(shoe_array, size=chunk_size)
                new_totals = split_card_val + new_cards

                dealer_totals = simulate_dealer_hand_vectorized(dealer_card_val, shoe_counts, chunk_size)

                win_conditions = (new_totals <= BLACKJACK) & ((dealer_totals > BLACKJACK) | (new_totals > dealer_totals))
                lose_conditions = (new_totals <= BLACKJACK) & (new_totals < dealer_totals)
                bust_conditions = (new_totals > BLACKJACK)

                split_ev += np.sum(win_conditions)
                split_ev -= np.sum(lose_conditions)
                split_ev -= np.sum(bust_conditions)

                if _ == 0:
                    checkpoint_means.append(split_ev / ((i + 1) * chunk_size))

        ev += split_ev / 2

    elapsed_time = time.time() - start_time
    print(f"Final EV for {action}: {ev / simulations:.5f}, Time: {elapsed_time:.2f}s")

    # Print checkpoint means in a single row
    benchmarks = " | ".join([f"{(i + 1) * 10}%: {mean:.5f}" for i, mean in enumerate(checkpoint_means)])
    print(f"Convergence Benchmarks (Mean EV at 10% checkpoints): [{benchmarks}]")

    return (ev / simulations) * RTP, elapsed_time, checkpoint_means

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

    # Sort by highest EV
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
        if action == best_action:
            print(f"    EVdiff: {Fore.MAGENTA}{ev_diff:.5f}{Style.RESET_ALL} vs {second_best_action}")

    print(f"\nOptimal Action: {best_action} ({times[best_action]:.2f} seconds)\n")
    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with a Persistent Shoe State\n")
    print("(Type '0' in the dealer/player/removal prompts to reset the shoe and start a new sequence)\n")

    # Initialize the shoe once
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
                "Enter Player's cards (e.g. 'T5', 'J9', '77') or 0 to reset: "
            ).strip().upper()

            if player_input == '0':
                shoe_counts = initialize_shoe_counts(NUM_DECKS)
                print("\nShoe has been reset! Starting a new hand...\n")
                continue

            if len(player_input) == 0:
                raise ValueError("Player's hand cannot be empty!")

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
                    numeric_shoe = build_numeric_shoe_array(shoe_counts)
                    if len(numeric_shoe) == 0:
                        raise ValueError("Shoe is empty, can't draw a card!")
                    drawn_val = random.choice(numeric_shoe)
                    for rank in ALL_RANKS:
                        if RANK_TO_VALUE[rank] == drawn_val and shoe_counts[rank] > 0:
                            remove_card_from_shoe(shoe_counts, rank)
                            player_cards.append(drawn_val)
                            print(f"\nDrew a '{rank}' for Double Down.")
                            break
                    print(f"Final hand after doubling: {player_cards} (Total: {hand_value(player_cards)})\n")
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
