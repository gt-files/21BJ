import random

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 6
SIMULATIONS = 10000  # Number of simulations for Monte Carlo

# Helper Functions
def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand(dealer_hand, shoe):
    """Simulates the dealer's hand and returns the final value."""
    while hand_value(dealer_hand) < DEALER_STAND:
        dealer_hand.append(random.choice(shoe))
    return hand_value(dealer_hand)

def monte_carlo_ev(player_cards, dealer_card, shoe, action, simulations=SIMULATIONS):
    """
    Perform Monte Carlo simulations to estimate the EV for a given action.
    Returns the EV of the action.
    """
    player_total = hand_value(player_cards)
    ev = 0

    for _ in range(simulations):
        shoe_copy = shoe[:]
        random.shuffle(shoe_copy)

        # Simulate action
        if action == "Stand":
            dealer_hand = [dealer_card]
            dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
            if dealer_total > BLACKJACK or player_total > dealer_total:
                ev += 1  # Win
            elif player_total < dealer_total:
                ev -= 1  # Lose

        elif action == "Hit":
            player_cards_hit = player_cards + [random.choice(shoe_copy)]
            new_total = hand_value(player_cards_hit)
            if new_total > BLACKJACK:
                ev -= 1  # Bust
            else:
                dealer_hand = [dealer_card]
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += 1  # Win
                elif new_total < dealer_total:
                    ev -= 1  # Lose

        elif action == "Double Down":
            player_cards_double = player_cards + [random.choice(shoe_copy)]
            new_total = hand_value(player_cards_double)
            bet = 2  # Doubling the bet
            if new_total > BLACKJACK:
                ev -= bet  # Bust
            else:
                dealer_hand = [dealer_card]
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += bet  # Win
                elif new_total < dealer_total:
                    ev -= bet  # Lose

        elif action == "Split":
            if len(player_cards) == 2 and (player_cards[0] == player_cards[1] or (player_cards[0] in [10, 11, 12, 13] and player_cards[1] in [10, 11, 12, 13])):
                # If the player has a pair, simulate each split hand.
                split_ev = 0
                for _ in range(2):  # Simulate both split hands
                    hand_copy = [player_cards[0], random.choice(shoe_copy)]
                    split_ev += monte_carlo_ev(hand_copy, dealer_card, shoe_copy, "Stand", simulations // 2)
                ev += split_ev / 2  # Average EV of both split hands

    return ev / simulations

# Main Gameplay Logic
def get_player_action(player_cards, dealer_card, shoe, is_first_turn=True):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit"]
    if is_first_turn:
        actions.append("Double Down")  # Only allowed on the first turn
        # Check for any 10-value pair to allow split (10, Jack, Queen, King)
        if len(player_cards) == 2 and any(card in [10, 11, 12, 13] for card in player_cards):
            actions.append("Split")

    evs = {action: monte_carlo_ev(player_cards, dealer_card, shoe, action) for action in actions}
    best_action = max(evs, key=evs.get)

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        print(f"  {action}: {ev:.2f}")
    print(f"Optimal Action: {best_action}")

    return best_action

def main():
    print("Blackjack Optimal Strategy Solver with Monte Carlo EV Calculation\n")
    shoe = DECK * NUM_DECKS  # Simulate a 6-deck shoe

    while True:
        dealer_card = int(input("Enter Dealer's visible card (2-11, where 11 is Ace): "))
        player_cards = list(map(int, input("Enter Player's cards (space-separated, use 11 for Ace): ").split()))
        if dealer_card < 2 or dealer_card > 11 or any(card < 1 or card > 11 for card in player_cards):
            print("Invalid input. Restarting hand...\n")
            continue

        while True:
            best_action = get_player_action(player_cards, dealer_card, shoe, is_first_turn=len(player_cards) == 2)
            if best_action == "Stand":
                print("\nYou chose to stand. Ending turn.")
                break

            if best_action == "Hit":
                new_card = int(input("\nEnter the value of the next card drawn (1-11): "))
                player_cards.append(new_card)
                if hand_value(player_cards) > BLACKJACK:
                    print(f"\nPlayer busted with a total of {hand_value(player_cards)}!")
                    break

            elif best_action == "Double Down":
                player_cards.append(random.choice(shoe))
                print(f"\nFinal hand after doubling down: {player_cards} (Total: {hand_value(player_cards)})")
                break

            elif best_action == "Split":
                print("\nYou chose to split!")
                # Split the hand into two separate hands
                player_card_1 = [player_cards[0], random.choice(shoe)]
                player_card_2 = [player_cards[1], random.choice(shoe)]
                print(f"Hand 1: {player_card_1} (Total: {hand_value(player_card_1)})")
                print(f"Hand 2: {player_card_2} (Total: {hand_value(player_card_2)})")
                break

        print("\nStarting next hand...\n")

if __name__ == "__main__":
    main()
