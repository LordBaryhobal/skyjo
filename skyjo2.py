#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
import paho.mqtt.client as mqtt
import threading, random, uuid, json, time

from player import Player
from card import Card
from player import State as PlayerState

MQTT_HOST = "127.0.0.1"
WIDTH, HEIGHT = 1800, 1000
H_WIDTH, H_HEIGHT = WIDTH/2, HEIGHT/2
T_WIDTH, T_HEIGHT = WIDTH/3, HEIGHT/3
Q_WIDTH, Q_HEIGHT = WIDTH/4, HEIGHT/4

class State:
    #Game
    QUIT = -1
    MAIN_MENU = 0
    WAITING_JOIN = 1
    WAITING_START = 2
    SERVER_LIST = 3
    PLAYING = 4

class TurnStep:
    DECK_DISCARD = 0
    PLACE_CARD = 1
    DISCARD_REVEAL = 2
    DELAY = 3

def on_message(client, userdata, msg):
    Game.instance.on_message(client, userdata, msg)

def on_connect(client, userdata, flags, rc):
    print("Connected")

def on_subscribe(client, userdata, mid, granted_qos):
    pass

def on_log(client, userdata, level, buff):
    print("[LOG] "+buff)

def loopThread():
    while Game.instance.state != State.QUIT:
        Game.instance.mqtt.loop()

class Game:
    ID = str(uuid.uuid4())
    MQTT_ROOT = "skyjo/"
    BUT_NORMAL = (127, 188, 102)
    BUT_HOVER = (153, 195, 136)
    BUT_CLICK = (101, 174, 73)
    
    NOT_RED = (214,60,75)
    NOT_ORANGE = (214,130,60)
    NOT_YELLOW = (214,210,60)
    NOT_GREEN = (102,214,60)
    
    instance = None
    layouts = [
        None,
        None,
        [5], # 2
        [2,8], # 3
        [2,5,8], # 4
        [1,3,7,9], # 5
        [1,3,5,7,9], # 6
        [1,3,4,6,7,9], # 7
        [1,3,4,5,6,7,9]  # 8
    ]
    
    def __init__(self):
        Game.instance = self
        
        self.state = State.MAIN_MENU
        self.turn_step = None
        self.cur_player = 0
        
        self.mqtt = mqtt.Client()
        
        self.mqtt.on_message = on_message
        self.mqtt.on_connect = on_connect
        self.mqtt.on_subscribe = on_subscribe
        self.mqtt.on_log = on_log
        
        self.mqtt.connect(MQTT_HOST)
        
        self.thread = threading.Thread(target=loopThread)
        self.thread.start()
        
        self.buttons = []
        self.players = {}
        self.players_id = []
        self.server_id = None
        self.is_server = False
        
        self.notifs = []
        
        self.deck_card = Card(None, (H_WIDTH - Card.WIDTH - 10, H_HEIGHT), 0, False)
        self.discard_card = Card(None, (H_WIDTH + Card.WIDTH + 10, H_HEIGHT), 0, True)
        
        self.began_last_turn = None
    
    def loop(self):
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.state = State.QUIT
                
                self.quit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.state == State.PLAYING:
                        player = self.players[self.ID]
                        
                        clicked = None
                        
                        if player.is_clicked(*event.pos):
                            card = player.click(*event.pos)
                            
                            if not card is None:
                                clicked = card
                                
                        
                        elif self.deck_card.is_clicked(*event.pos):
                            clicked = "deck"
                            
                        elif self.discard_card.is_clicked(*event.pos):
                            clicked = "discard"
                        
                        if not clicked is None:
                            self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"click", "id":self.ID, "card":clicked}))
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    for button in self.buttons:
                        rect = button[1]
                        if rect[0] <= event.pos[0] < rect[0]+rect[2] and rect[1] <= event.pos[1] < rect[1]+rect[3]:
                            button[2](self, *button[3])
    
    def display(self, win, clock):
        pygame.display.set_caption(f"Skyjo - {clock.get_fps():.2f}fps")
        self.buttons = []
        
        win.fill(0)
        
        if self.state == State.QUIT:
            text = self.font.render("Goodbye", True, (255,255,255))
            win.blit(text, [H_WIDTH-text.get_width()/2, H_HEIGHT-text.get_height()/2])
        
        elif self.state == State.MAIN_MENU:
            title = self.font.render("Skyjo", True, (255,255,255))
            win.blit(title, [H_WIDTH-title.get_width()/2, Q_HEIGHT])
            
            self.buttons = self.main_buttons
        
        elif self.state == State.SERVER_LIST:
            self.buttons.append(self.return_button)
            
            y = T_HEIGHT
            for server in self.servers:
                self.buttons.append((
                    server,
                    [T_WIDTH, y, T_WIDTH, 50],
                    Game.but_join_server,
                    (server,)
                ))
                
                y += 75
        
        elif self.state == State.PLAYING:
            is_turn = (self.cur_player == self.players_id.index(self.ID))
            
            self.players[self.ID].highlight = False
            if is_turn and self.turn_step in [TurnStep.DISCARD_REVEAL, TurnStep.PLACE_CARD]:
                self.players[self.ID].highlight = True
            
            for player in self.players.values():
                player.display(win)
            
            self.discard_card.num = self.discard[-1]
            
            self.deck_card.highlighted = False
            self.discard_card.highlighted = False
            if is_turn:
                if self.turn_step == TurnStep.DECK_DISCARD:
                    self.deck_card.highlighted = True
                    self.discard_card.highlighted = True
                
                elif self.turn_step == TurnStep.DISCARD_REVEAL:
                    self.discard_card.highlighted = True
            
            self.deck_card.display(win)
            self.discard_card.display(win)
        
        elif self.state in [State.WAITING_JOIN, State.WAITING_START]:
            self.buttons.append(self.return_button)
            
            title = self.font.render("Players", True, (255,255,255))
            win.blit(title, [H_WIDTH-title.get_width()/2, Q_HEIGHT])
            
            y = T_HEIGHT
            for player in self.players_id:
                text = self.font.render(player, True, (255,255,255))
                
                win.blit(text, [H_WIDTH-text.get_width()/2, y-text.get_height()/2])
                
                y += 75
        
        if self.state == State.WAITING_JOIN:
            if len(self.players_id) >= 2:
                self.buttons.append((
                    "Start",
                    [T_WIDTH, HEIGHT-Q_HEIGHT, T_WIDTH, 50],
                    Game.but_start_game,
                    ()
                ))
        
        #pygame.draw.line(win, (255,255,255), [H_WIDTH, 0], [H_WIDTH, HEIGHT])
        
        mouse = pygame.mouse.get_pos()
        mouse_but = pygame.mouse.get_pressed()
        
        for button in self.buttons:
            text = self.font.render(button[0], True, (0,0,0))
            col = self.BUT_NORMAL
            rect = button[1]
            
            if rect[0] <= mouse[0] < rect[0]+rect[2] and rect[1] <= mouse[1] < rect[1]+rect[3]:
                col = self.BUT_HOVER
                
                if mouse_but[0]:
                    col = self.BUT_CLICK
            
            pygame.draw.rect(win, col, rect)
            win.blit(text, [rect[0]+rect[2]/2-text.get_width()/2, rect[1]+rect[3]/2-text.get_height()/2])
        
        cur_time = time.time()
        y = 10
        for notif in self.notifs:
            text, col, t1 = notif
            diff = cur_time-t1
            
            text = self.font.render(text, True, (255,255,255))
            
            offset = 0
            
            if diff > 3:
                offset = (diff-3)/1.5 * 50
                
                if diff > 5:
                    notif[0] = None
            
            y -= offset
            
            pygame.draw.rect(win, col, [WIDTH-text.get_width()-30, y, text.get_width()+20, 40])
            win.blit(text, [WIDTH-text.get_width()-20, y+20-text.get_height()/2])
            y += 50
        
        self.notifs = list(filter(lambda n: n[0], self.notifs))
        
        pygame.display.flip()
    
    def start_game(self):
        layout = [0]+self.layouts[len(self.players_id)]
        positions = [
            ((H_WIDTH, HEIGHT), 0),
            
            ((0, HEIGHT-Q_HEIGHT), 90),
            ((0, H_HEIGHT), 90),
            ((0, Q_HEIGHT), 90),
            
            ((Q_WIDTH, 0), 180),
            ((H_WIDTH, 0), 180),
            ((WIDTH-Q_WIDTH, 0), 180),
            
            ((WIDTH, Q_HEIGHT), 270),
            ((WIDTH, H_HEIGHT), 270),
            ((WIDTH, HEIGHT-Q_HEIGHT), 270)
        ]
        
        i = self.players_id.index(self.ID)
        players_id = self.players_id[i:] + self.players_id[:i]
        
        self.players = {}
        
        self.discard = []
        self.cards = [-2]*5 + [0]*15 + list(range(-1,13))*10
        
        random.shuffle(self.cards)
        
        for i in range(len(players_id)):
            #nums = [random.randint(-2,12) for j in range(12)]
            nums = self.cards[:12] if self.is_server else [None]*12
            self.cards = self.cards[12:]
            
            player = Player("Player {i+1}", positions[layout[i]][0], positions[layout[i]][1], nums)
            self.players[players_id[i]] = player
        
        self.deck = self.cards
        
        self.discard.append(self.cards.pop(0))
        self.players[self.ID].state = PlayerState.STARTED
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"state", "id":self.ID, "state":PlayerState.STARTED}))
    
    def end_game(self):
        scores = {}
        for player_id in self.players_id:
            player = self.players[player_id]
            player.flip_all()
            scores[player_id] = player.get_score()
        
        self.send_cards()
        
        began_last_id = self.players_id[self.began_last_turn]
        print(scores)
        
        print("The End")
    
    def but_host(self, *args):
        self.server_id = self.ID
        self.state = State.WAITING_JOIN
        self.mqtt.subscribe(Game.MQTT_ROOT+"servers",1)
        self.mqtt.subscribe(Game.MQTT_ROOT+"server/"+self.server_id,1)
        self.players_id = [self.ID]
    
    def but_join(self, *args):
        self.mqtt.subscribe(Game.MQTT_ROOT+"servers",1)
        self.mqtt.publish(Game.MQTT_ROOT+"servers", json.dumps({"cmd":"searching"}))
        
        self.state = State.SERVER_LIST
        self.servers = []
    
    def but_join_server(self, *args):
        self.server_id = args[0]
        
        self.mqtt.subscribe(Game.MQTT_ROOT+"server/"+self.server_id,1)
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"join", "id": self.ID}))
        
        self.state = State.WAITING_START
        self.players_id = [self.ID]
    
    def but_return(self, *args):
        if self.state == State.SERVER_LIST:
            self.state = State.MAIN_MENU
        
        elif self.state == State.WAITING_JOIN:
            self.state = State.MAIN_MENU
            self.quit()
        
        elif self.state == State.WAITING_START:
            self.state = State.SERVER_LIST
            self.quit()
    
    def but_start_game(self, *args):
        self.is_server = True
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"start"}))
    
    def quit(self):
        if not self.server_id is None:
            self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"quit", "id": self.ID}))
    
    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())
        print(payload["cmd"])
        
        if self.state == State.WAITING_JOIN:
            if payload["cmd"] == "searching":
                self.mqtt.publish(Game.MQTT_ROOT+"servers", json.dumps({"cmd":"server","id":self.ID}))
            
            elif payload["cmd"] == "join":
                self.notify("Player joined", Game.NOT_GREEN)
                self.players_id.append(payload["id"])
                
                self.send_players()
                
                if len(self.players_id) == 8:
                    self.start_game()
            
            elif payload["cmd"] == "quit":
                self.notify("Player left", Game.NOT_ORANGE)
                self.players_id.remove(payload["id"])
                self.send_players()
        
        elif self.state == State.SERVER_LIST:
            if payload["cmd"] == "server":
                server_id = payload["id"]
            
                if not server_id in self.servers:
                    self.servers.append(server_id)
        
        elif self.state == State.WAITING_START:
            if payload["cmd"] == "players":
                self.players_id = payload["players"]
            
            elif payload["cmd"] == "join":
                self.notify("Player joined", Game.NOT_GREEN)
            
            elif payload["cmd"] == "quit":
                self.notify("Player left", Game.NOT_ORANGE)
        
        elif self.state == State.PLAYING:
            if payload["cmd"] == "cards":
                if not self.is_server:
                    self.deck = payload["deck"]
                    self.discard = payload["discard"]
                    
                    for player_id in self.players_id:
                        player = self.players[player_id]
                        prev_state = player.state
                        
                        player.set_cards(payload["players"][player_id])
                        
                        if prev_state != player.state:
                            self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"state", "id":player_id, "state":player.state}))
            
            elif payload["cmd"] == "state":
                self.players[payload["id"]].state = payload["state"]
                print(f"player {payload['id']} state -> {payload['state']}")
                
                if self.is_server:
                    if self.turn_step is None:
                        if len(list(filter(lambda p: p.state!=PlayerState.STARTED, self.players.values()))) == 0:
                            self.send_cards()
                        
                        elif len(list(filter(lambda p: p.state!=PlayerState.READY, self.players.values()))) == 0:
                            self.start_turn()
            
            elif payload["cmd"] == "turn":
                self.turn_step = payload["turn_step"]
                self.cur_player = payload["cur_player"]
                self.began_last_turn = payload["began_last_turn"]
                
                if not self.began_last_turn is None:
                    self.players[self.players_id[self.cur_player-1]].finished = True
            
            if self.is_server:
                if payload["cmd"] == "click":
                    card = payload["card"]
                    player = self.players[payload["id"]]
                    
                    if self.turn_step == None:
                        if not card in ["deck","discard"] and player.get_flipped_count() < 2:
                            player.cards[card[1]][card[0]].flip = True
                            self.send_cards()
                    
                    else:
                        if payload["id"] == self.players_id[self.cur_player]:
                            if card == "deck":
                                if self.turn_step == TurnStep.DECK_DISCARD:
                                    self.discard.append(self.deck.pop(-1))
                                    self.turn_step = TurnStep.DISCARD_REVEAL
                                    self.send_cards()
                                    self.send_turn_info()
                            
                            elif card == "discard":
                                if self.turn_step in [TurnStep.DECK_DISCARD, TurnStep.DISCARD_REVEAL]:
                                    self.turn_step = TurnStep.PLACE_CARD
                                    self.send_turn_info()
                            
                            else:
                                x, y = card
                                if self.turn_step == TurnStep.PLACE_CARD:
                                    new = self.discard.pop(-1)
                                    old = player.cards[y][x].num
                                    player.cards[y][x].num = new
                                    player.cards[y][x].flip = True
                                    self.discard.append(old)
                                    
                                    self.end_turn()
                                
                                elif self.turn_step == TurnStep.DISCARD_REVEAL:
                                    card = player.cards[y][x]
                                    if not card.flip:
                                        card.flip = True
                                        self.end_turn()
                                
        
        if self.state in [State.WAITING_JOIN, State.WAITING_START]:
            if payload["cmd"] == "start":
                self.state = State.PLAYING
                self.start_game()
    
    def send_players(self):
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"players", "players": self.players_id}))
    
    def send_cards(self):
        result = {"cmd":"cards", "players": {}}
        
        for player_id in self.players_id:
            result["players"][player_id] = self.players[player_id].get_cards()
        
        result["discard"] = self.discard
        result["deck"] = self.deck
        
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps(result))
    
    def notify(self, text, color):
        self.notifs.append([text, color, time.time()])
    
    def start_turn(self):
        self.turn_step = TurnStep.DECK_DISCARD
        self.send_turn_info()
        self.send_cards()
    
    def end_turn(self):
        player = self.players[self.players_id[self.cur_player]]
        
        for x in range(4):
            nums, flips, removed = list(zip(*[ (player.cards[y][x].num, player.cards[y][x].flip, player.cards[y][x].removed) for y in range(3)]))
            
            if all([n == nums[0] for n in nums]) and all(flips) and not any(removed):
                for y in range(3):
                    player.cards[y][x].removed = True
                    self.discard.append(nums[0])
        
        if self.began_last_turn is None:
            if player.get_non_flipped_count() == 0:
                self.began_last_turn = self.cur_player
        
        self.cur_player += 1
        self.cur_player %= len(self.players_id)
        
        if self.began_last_turn == self.cur_player:
            self.end_game()
        
        else:
            self.start_turn()
    
    def send_turn_info(self):
        self.mqtt.publish(Game.MQTT_ROOT+"server/"+self.server_id, json.dumps({"cmd":"turn", "turn_step": self.turn_step, "cur_player": self.cur_player, "began_last_turn": self.began_last_turn}))
    
    return_button = ["<", [20, 20, 50, 50], but_return, ()]
    
    main_buttons = [
        ["Host", [H_WIDTH-150, H_HEIGHT-40, 300, 80], but_host, ()],
        ["Join", [H_WIDTH-150, H_HEIGHT+80, 300, 80], but_join, ()]
    ]

if __name__ == "__main__":
    pygame.init()
    Game.font = pygame.font.SysFont("ubuntu", 30)
    
    w = pygame.display.set_mode([WIDTH, HEIGHT])
    
    clock = pygame.time.Clock()
    
    game = Game()
    
    while game.state != State.QUIT:
        game.display(w, clock)
        game.loop()
        
        clock.tick(60)