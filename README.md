# Skyjo

Skyjo is a multiplayer card game (2 to 8 players). At the beginning of the game each player receives 12 cards (4x3) face down.

Each player flips 2 of their cards. On a player's turn, they have multiple choices:
- Pick the top card on the discard pile
- Pick the top card on the draw pile

If they draw a card from the draw pile, they can:
- discard it and then reveal one of their face-down cards
- keep it and replace one of their cards which is discarded. The replaced card can be any card, either face-down or face-up

If they pick the top card from the discard pile, they exchange it with one of their cards, which is discard. The replaced card can be any card, either face-down or face-up.

If 3 cards of the same number are aligned vertically, the entire column is discarded.

When a player reveals their last card, the final turn is started. Each remaining player can play one last time.

When the game is finished, all the cards are revealed and the scores are calculated by adding all the numbers for each player. If the player who ended the game (i.e. who started the last turn) doesn't strictly have the lowest score, his score is doubled.

In the game, there are:
- 5x "-2" cards
- 15x "0" cards
- 10x cards for each number between -1 and 12 (excluding 0)

## Requirements

- Python 3 or higher
- Python modules: `pygame`, `paho-mqtt`
- An MQTT broker must be set up and accessible by all players
- Change the IP address in `MQTT_HOST` to the address of the broker