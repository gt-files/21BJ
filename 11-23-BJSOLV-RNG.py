import random
import matplotlib.pyplot as plt

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Single deck
SIMULATIONS = 10  # Number of Monte Carlo simulations
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}  # Card mapping
BLACKJACK_PAYOUT = 1.5  # 3:2 payout for blackjack

# Helper Functions
def hand_value(cards):
    """Calculate the total value of a hand, accounting for soft aces."""
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand(dealer_hand):
    """Simulates the dealer's hand based on standard online casino rules."""
    while True:
        value = hand_value(dealer_hand)
        if value < DEALER_STAND or (value == DEALER_STAND and 11 in dealer_hand):
            dealer_hand.append(random.choice(DECK))
        else:
            break
    return hand_value(dealer_hand)

def monte_carlo_ev(player_cards, dealer_card, action, simulations=SIMULATIONS):
    """
    Perform Monte Carlo simulations to estimate the EV for a given action.
    Returns the EV of the action.
    """
    ev = 0

    for _ in range(simulations):
        player_hand = player_cards[:]
        dealer_hand = [dealer_card]

        if action == "Stand":
            dealer_total = simulate_dealer_hand(dealer_hand)
            player_total = hand_value(player_hand)
            if player_total > dealer_total or dealer_total > BLACKJACK:
                ev += 1  # Win
            elif player_total < dealer_total:
                ev -= 1  # Lose

        elif action == "Hit":
            player_hand.append(random.choice(DECK))
            player_total = hand_value(player_hand)
            if player_total > BLACKJACK:
                ev -= 1  # Bust
            else:
                dealer_total = simulate_dealer_hand(dealer_hand)
                if player_total > dealer_total or dealer_total > BLACKJACK:
                    ev += 1  # Win
                elif player_total < dealer_total:
                    ev -= 1  # Lose

        elif action == "Double Down":
            player_hand.append(random.choice(DECK))
            player_total = hand_value(player_hand)
            bet = 2
            if player_total > BLACKJACK:
                ev -= bet  # Bust
            else:
                dealer_total = simulate_dealer_hand(dealer_hand)
                if player_total > dealer_total or dealer_total > BLACKJACK:
                    ev += bet  # Win
                elif player_total < dealer_total:
                    ev -= bet  # Lose

    return ev / simulations

# Main Solver Logic
def get_player_action(player_cards, dealer_card):
    """Determines the player's optimal action based on Monte Carlo EV."""
    actions = ["Stand", "Hit", "Double Down"]

    # Only offer "Double Down" on two-card hands
    if len(player_cards) != 2:
        actions.remove("Double Down")

    evs = {action: monte_carlo_ev(player_cards, dealer_card, action) for action in actions}
    best_action = max(evs, key=evs.get)

    print("\nPlayer Cards:", player_cards, "Total:", hand_value(player_cards))
    print("Dealer Card:", dealer_card)
    print("Expected Values (EVs):")
    for action, ev in evs.items():
        print(f"  {action}: {ev:.5f}")
    print(f"Optimal Action: {best_action}")

    return best_action

def simulate_game():
    """Simulate a single hand of online RNG blackjack."""
    player_cards = [random.choice(DECK), random.choice(DECK)]
    dealer_card = random.choice(DECK)

    # Check for natural blackjack
    if hand_value(player_cards) == BLACKJACK:
        print("\nPlayer has a natural blackjack!")
        return BLACKJACK_PAYOUT

    # Determine player's optimal action
    while True:
        action = get_player_action(player_cards, dealer_card)

        if action == "Stand":
            break
        elif action == "Hit":
            player_cards.append(random.choice(DECK))
            if hand_value(player_cards) > BLACKJACK:
                print(f"\nPlayer busted with a total of {hand_value(player_cards)}!")
                return -1  # Bust
        elif action == "Double Down":
            player_cards.append(random.choice(DECK))
            print(f"\nFinal hand after doubling down: {player_cards} (Total: {hand_value(player_cards)})")
            break

    # Dealer plays
    dealer_hand = [dealer_card]
    dealer_total = simulate_dealer_hand(dealer_hand)
    player_total = hand_value(player_cards)

    print("\nFinal Results:")
    print(f"  Player Hand: {player_cards} (Total: {player_total})")
    print(f"  Dealer Hand: {dealer_hand} (Total: {dealer_total})")

    if dealer_total > BLACKJACK or player_total > dealer_total:
        return 1  # Win
    elif player_total < dealer_total:
        return -1  # Lose
    else:
        return 0  # Push

def main():
    print("Online RNG Blackjack Solver and Simulator\n")
    results = [simulate_game() for _ in range(SIMULATIONS)]

    # Plot results distribution
    plt.hist(results, bins=range(-2, 3), align='left', edgecolor='black', alpha=0.7)
    plt.title("Simulation Outcomes of RNG Blackjack")
    plt.xlabel("Result (-1: Lose, 0: Push, 1: Win, 1.5: Blackjack)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
