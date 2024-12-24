import random
import tkinter as tk
from tkinter import ttk, messagebox

# Constants
BLACKJACK = 21
DEALER_STAND = 17
DECK = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Card values for a single deck
NUM_DECKS = 8
SIMULATIONS = 10000
FACE_CARD_MAPPING = {'T': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 11}

# Helper Functions
def hand_value(cards):
    total = sum(cards)
    aces = cards.count(11)
    while total > BLACKJACK and aces:
        total -= 10
        aces -= 1
    return total

def simulate_dealer_hand(dealer_hand, shoe):
    while hand_value(dealer_hand) < DEALER_STAND:
        dealer_hand.append(random.choice(shoe))
    return hand_value(dealer_hand)

def monte_carlo_ev(player_cards, dealer_card, shoe, action, simulations=SIMULATIONS):
    player_total = hand_value(player_cards)
    ev = 0

    for _ in range(simulations):
        shoe_copy = shoe[:]
        random.shuffle(shoe_copy)

        if action == "Stand":
            dealer_hand = [dealer_card]
            dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
            if dealer_total > BLACKJACK or player_total > dealer_total:
                ev += 1
            elif player_total < dealer_total:
                ev -= 1

        elif action == "Hit":
            player_cards_hit = player_cards + [random.choice(shoe_copy)]
            new_total = hand_value(player_cards_hit)
            if new_total > BLACKJACK:
                ev -= 1
            else:
                dealer_hand = [dealer_card]
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += 1
                elif new_total < dealer_total:
                    ev -= 1

        elif action == "Double Down":
            player_cards_double = player_cards + [random.choice(shoe_copy)]
            bet = 2
            new_total = hand_value(player_cards_double)
            if new_total > BLACKJACK:
                ev -= bet
            else:
                dealer_hand = [dealer_card]
                dealer_total = simulate_dealer_hand(dealer_hand, shoe_copy)
                if dealer_total > BLACKJACK or new_total > dealer_total:
                    ev += bet
                elif new_total < dealer_total:
                    ev -= bet

        elif action == "Split":
            if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
                split_ev = 0
                for _ in range(2):
                    hand_copy = [player_cards[0], random.choice(shoe_copy)]
                    split_ev += monte_carlo_ev(hand_copy, dealer_card, shoe_copy, "Stand", simulations // 2)
                ev += split_ev / 2

    return ev / simulations

# GUI Application
def calculate_optimal_action():
    try:
        dealer_card_input = dealer_card_var.get().strip().upper()
        if dealer_card_input in FACE_CARD_MAPPING:
            dealer_card = FACE_CARD_MAPPING[dealer_card_input]
        elif dealer_card_input.isdigit() and 2 <= int(dealer_card_input) <= 11:
            dealer_card = int(dealer_card_input)
        else:
            raise ValueError("Invalid dealer card!")

        player_cards_input = player_cards_var.get().strip().upper().split()
        player_cards = []
        for card in player_cards_input:
            if card in FACE_CARD_MAPPING:
                player_cards.append(FACE_CARD_MAPPING[card])
            elif card.isdigit() and 2 <= int(card) <= 11:
                player_cards.append(int(card))
            else:
                raise ValueError("Invalid player card!")

        shoe = DECK * NUM_DECKS
        actions = ["Stand", "Hit", "Double Down"]
        if len(player_cards) == 2 and player_cards[0] == player_cards[1]:
            actions.append("Split")

        evs = {action: monte_carlo_ev(player_cards, dealer_card, shoe, action) for action in actions}
        best_action = max(evs, key=evs.get)

        # Update results in GUI
        result_text = "\n".join([f"{action}: {ev:.4f}" + (" <-- Best Move" if action == best_action else "") for action, ev in evs.items()])
        result_var.set(f"Player Cards: {player_cards}, Total: {hand_value(player_cards)}\nDealer Card: {dealer_card}\n\n{result_text}\n\nOptimal Action: {best_action}")

    except ValueError as e:
        messagebox.showerror("Input Error", str(e))

# GUI Setup
root = tk.Tk()
root.title("Blackjack EV Calculator")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

dealer_card_var = tk.StringVar()
player_cards_var = tk.StringVar()
result_var = tk.StringVar()

ttk.Label(frame, text="Dealer Card (2-11 or T/J/Q/K/A):").grid(row=0, column=0, sticky=tk.W, pady=5)
dealer_card_entry = ttk.Entry(frame, textvariable=dealer_card_var)
dealer_card_entry.grid(row=0, column=1, sticky=tk.E)

ttk.Label(frame, text="Player Cards (space-separated, 2-11 or T/J/Q/K/A):").grid(row=1, column=0, sticky=tk.W, pady=5)
player_cards_entry = ttk.Entry(frame, textvariable=player_cards_var)
player_cards_entry.grid(row=1, column=1, sticky=tk.E)

calculate_button = ttk.Button(frame, text="Calculate", command=calculate_optimal_action)
calculate_button.grid(row=2, column=0, columnspan=2, pady=10)

result_label = ttk.Label(frame, textvariable=result_var, justify=tk.LEFT, wraplength=400)
result_label.grid(row=3, column=0, columnspan=2, sticky=tk.W)

# Start the GUI loop
root.mainloop()
