#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
from card import Card

class State:
    NOT_READY = 0
    STARTED = 1
    READY = 2

class Player:
    HIGHLIGHT = (255,255,255)
    
    def __init__(self, name, pos, rot, cards):
        self.state = State.NOT_READY
        self.name = name
        self.pos = pos
        self.rot = rot
        
        self.highlight = False
        self.finished = False
        
        self.cards = []
        
        sx, sy = self.offset(self.rot, -1.5*Card.WIDTH - 15, -2.5*Card.HEIGHT-30)
        sx += self.pos[0]
        sy += self.pos[1]
        
        for y in range(3):
            self.cards.append([])
            for x in range(4):
                num = cards[x+y*4]
                
                pos2 = self.offset(self.rot, x*(Card.WIDTH+10), y*(Card.HEIGHT+10))
                
                card = Card(num, [sx+pos2[0], sy+pos2[1]], self.rot, False)
                
                self.cards[-1].append(card)
    
    def offset(self, rot, x, y):
        cos = [1, 0, -1, 0][rot//90]
        sin = [0, 1, 0, -1][rot//90]
        
        return (x*cos - y*sin, x*sin + y*cos)
    
    def display(self, win):
        if self.highlight:
            pos_x, pos_y = self.offset(self.rot, 0, -1.5*Card.HEIGHT -20)
            pos_x += self.pos[0]
            pos_y += self.pos[1]
            hw, hh = 2*Card.WIDTH+15, 1.5*Card.HEIGHT+10
            
            if self.rot % 180 == 90:
                hw, hh = hh, hw
            
            pygame.draw.rect(win, self.HIGHLIGHT, [pos_x-hw-3, pos_y-hh-3, 2*hw+6, 2*hh+6], 6)
        
        for y in range(3):
            for x in range(4):
                self.cards[y][x].display(win)
        
        if self.finished:
            text = Game.font.render("Finished", True, (255,255,255))
            
            x, y = self.offset(self.rot, 0, -3*Card.HEIGHT-40-text.get_height()/2)
            x += self.pos[0]
            y += self.pos[1]
            
            text = pygame.transform.rotate(text, -self.rot)
            win.blit(text, [x-text.get_width()/2,y-text.get_height()/2])
        
    
    def is_clicked(self, x, y):
        pos_x, pos_y = self.offset(self.rot, 0, -1.5*Card.HEIGHT -20)
        pos_x += self.pos[0]
        pos_y += self.pos[1]
        hw, hh = 2*Card.WIDTH+15, 1.5*Card.HEIGHT+10
        
        if self.rot % 180 == 90:
            hw, hh = hh, hw
        
        return (pos_x-hw <= x < pos_x+hw) and (pos_y-hh <= y < pos_y+hh)
    
    def click(self, x, y):
        for row in range(3):
            for col in range(4):
                card = self.cards[row][col]
                if card.is_clicked(x, y):
                    return (col, row)
        
        return None
    
    def get_cards(self):
        cards = []
        
        for y in range(3):
            for x in range(4):
                card = self.cards[y][x]
                cards.append((card.num, card.flip, card.removed))
        
        return cards
    
    def set_cards(self, cards):
        for i in range(len(cards)):
            x,y = i%4, i//4
            num, flip, removed = cards[i]
            self.cards[y][x].num = num
            self.cards[y][x].flip = flip
            self.cards[y][x].removed = removed
        
        if self.state == State.STARTED:
            if self.get_flipped_count() == 2:
                self.state = State.READY
    
    def get_flipped_count(self):
        count = 0
        for y in range(3):
            for x in range(4):
                if self.cards[y][x].flip:
                    count += 1
        
        return count
    
    def get_non_flipped_count(self):
        count = 0
        for y in range(3):
            for x in range(4):
                if not self.cards[y][x].flip:
                    count += 1
        
        return count
    
    def flip_all(self):
        for y in range(3):
            for x in range(4):
                self.cards[y][x].flip = True
    
    def get_score(self):
        score = 0
        
        for y in range(3):
            for x in range(4):
                card = self.cards[y][x]
                if not card.removed:
                    score += card.num
        
        return score