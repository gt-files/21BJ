import random
from colorama import Fore, Style, init
import time

# Initialize colorama
init()

# Constants
BLACKJACK = 21
DEALER_STAND = 17
NUM_DECKS = 6
SIMULATIONS = 100000  # <= You can reduce this for testing
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
            # We only need one copy here for the probability distribution,
            # but to approximate the correct distribution *with replacement*,
            # you could just store a single copy per rank. However, to maintain
            # a ratio roughly consistent with the real shoe, we keep multiple copies.
            # (You can choose to keep only one, if you like, but it will slightly alter
            # the distribution for large decks. Below we keep them all.)
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
    Uses random draws *with replacement* from the shoe distribution.
    Returns a list of final totals (one per simulation).
    """

    # Precompute a list of possible card draws from the shoe
    shoe_list = build_shoe_list(shoe_counts)

    # final_totals[i] = final total of dealer in simulation i
    final_totals = [0] * num_simulations

    for i in range(num_simulations):
        # Start the dealer's hand with just the visible card
        dealer_cards = [dealer_card_val]
        
        # Keep hitting until total >= DEALER_STAND or bust
        while True:
            total = hand_value(dealer_cards)
            if total < DEALER_STAND:
                # draw one card from shoe_list
                draw_val = random.choice(shoe_list)
                dealer_cards.append(draw_val)
            else:
                # stand or bust
                final_totals[i] = total
                break

    return final_totals

def monte_carlo_ev(player_cards, dealer_card_val, shoe_counts, action, simulations=SIMULATIONS):
    """
    Estimate the EV for a given action using simple Monte Carlo simulations.
    'player_cards' = list of integer values for player's initial cards
    'dealer_card_val' = integer value for dealer's visible card
    'shoe_counts' = current shoe state
    'action' = 'Stand', 'Hit', 'Double Down', or 'Split'
    'simulations' = how many total simulations to run
    """

    player_total = hand_value(player_cards)
    ev = 0
    checkpoint_means = []

    print(f"\nAction: {action}, Player Total: {player_total}, Dealer Card: {dealer_card_val}")

    start_time = time.time()
    # We'll do the simulations in 10 chunks to measure convergence
    chunk_size = simulations // 10

    # Helper for computing EV chunk by chunk
    def process_results_for_stand_like(player_t, dealer_totals_list, multiplier=1):
        """
        For standard stand/hit/double logic: 
          Win if dealer busts or (player > dealer)
          Lose if player < dealer
          If bust, immediate loss
        multiplier is used for Double Down (2x) or normal (1x).
        Returns the net contribution to EV in that chunk.
        """
        # If the player's hand is already > 21, it's always a bust
        if player_t > BLACKJACK:
            return -multiplier * len(dealer_totals_list)

        chunk_ev = 0
        for d_total in dealer_totals_list:
            if d_total > BLACKJACK:  
                # Dealer bust
                chunk_ev += multiplier
            else:
                # Compare totals
                if player_t > d_total:
                    chunk_ev += multiplier
                elif player_t < d_total:
                    chunk_ev -= multiplier
                # tie => 0
        return chunk_ev

    if action == "Stand":
        for i in range(10):
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
            ev_chunk = process_results_for_stand_like(player_total, dealer_totals, multiplier=1)
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Hit":
        for i in range(10):
            # Draw new card for the player, then see final result
            shoe_list = build_shoe_list(shoe_counts)
            # Perform 'chunk_size' draws for the player
            new_totals = []
            for _ in range(chunk_size):
                draw_val = random.choice(shoe_list)
                new_totals.append(player_total + draw_val)

            # Then simulate dealer
            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)

            # Evaluate wins/losses
            ev_chunk = 0
            for p_t, d_t in zip(new_totals, dealer_totals):
                if p_t > BLACKJACK:
                    # player bust
                    ev_chunk -= 1
                else:
                    # compare p_t and d_t
                    if d_t > BLACKJACK or p_t > d_t:
                        ev_chunk += 1
                    elif p_t < d_t:
                        ev_chunk -= 1
                    # tie => 0
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Double Down":
        for i in range(10):
            shoe_list = build_shoe_list(shoe_counts)
            new_totals = []
            for _ in range(chunk_size):
                draw_val = random.choice(shoe_list)
                new_totals.append(player_total + draw_val)

            dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)

            # Evaluate wins/losses (2x stakes)
            ev_chunk = 0
            for p_t, d_t in zip(new_totals, dealer_totals):
                if p_t > BLACKJACK:
                    # bust -> lose 2
                    ev_chunk -= 2
                else:
                    if d_t > BLACKJACK or p_t > d_t:
                        ev_chunk += 2
                    elif p_t < d_t:
                        ev_chunk -= 2
                    # tie => 0
            ev += ev_chunk
            checkpoint_means.append(ev / ((i + 1) * chunk_size))

    elif action == "Split":
        # For the sake of simplicity, do 2 separate hands, 
        # and average their results. We'll do chunk by chunk inside a loop.
        split_ev_accumulator = 0
        # We know both split hands have the same single card as the original pair
        split_card_val = player_cards[0]

        for split_index in range(2):
            # 2 separate hands
            hand_ev = 0
            for i in range(10):
                shoe_list = build_shoe_list(shoe_counts)
                new_totals = []
                for _ in range(chunk_size):
                    draw_val = random.choice(shoe_list)
                    new_totals.append(split_card_val + draw_val)

                dealer_totals = simulate_dealer_hands(dealer_card_val, shoe_counts, chunk_size)
                
                # Evaluate 1 hand’s results
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

                # For the *first* of the two split hands, store intermediate checkpoints
                if split_index == 0:
                    checkpoint_means.append(hand_ev / ((i + 1) * chunk_size))
            
            # Add to total for both hands
            split_ev_accumulator += hand_ev

        # Average EV for the two split hands
        # (hand_ev is the total net; dividing by chunk_size * 10 gives average per simulation
        #  but we want to combine both hands, so we do total/2 in the final step.)
        ev = split_ev_accumulator / 2

    elapsed_time = time.time() - start_time
    # For uniformity with other actions, 'ev' is total net outcomes over 'simulations'
    # so final EV is (ev / simulations).
    # Then we multiply by RTP
    final_ev = (ev / simulations) * RTP

    print(f"Final EV for {action}: {final_ev:.5f}, Time: {elapsed_time:.2f}s")

    # Print checkpoint means in a single row (only relevant if we collected them)
    if checkpoint_means:
        benchmarks = " | ".join(
            [f"{(i + 1) * 10}%: {val:.5f}" for i, val in enumerate(checkpoint_means)]
        )
        print(f"Convergence Benchmarks (Mean EV at 10% checkpoints): [{benchmarks}]")
    else:
        print("No convergence benchmarks available for this action.")

    return final_ev, elapsed_time, checkpoint_means

def get_player_action(player_cards, dealer_card_val, shoe_counts, is_first_turn=True):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit"]
    if is_first_turn:
        actions.append("Double Down")
    # Only consider splitting if exactly 2 cards, same value
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
    # second best
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

            # Now do an optimal action loop (like a real hand)
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
                    shoe_list = build_shoe_list(shoe_counts)
                    if not shoe_list:
                        raise ValueError("Shoe is empty, can't draw a card!")
                    drawn_val = random.choice(shoe_list)
                    # Find a rank in the shoe to remove (matching drawn_val)
                    # We'll remove the first match
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
