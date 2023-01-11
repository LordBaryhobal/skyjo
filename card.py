#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame

class Card:
    COLORS = [
        (136,56,233),
        (71,79,180),
        (112,170,244),
        (124,179,114),
        (253,241,123),
        (233,56,62)
    ]
    
    HIGHLIGHT = (255,255,255)
    
    WIDTH = 57
    HEIGHT = 88
    
    def __init__(self, num, pos, rot, flip=False):
        self.num = num
        self.pos = pos
        self.rot = rot
        self.flip = flip
        self.highlighted = False
        self.removed = False
    
    def display(self, win):
        if self.removed:
            return
        
        col = Card.COLORS[0]
        
        if self.flip and not self.num is None:
            if self.num < 0:
                col = Card.COLORS[1]
            elif self.num == 0:
                col = Card.COLORS[2]
            elif self.num <= 4:
                col = Card.COLORS[3]
            elif self.num <= 8:
                col = Card.COLORS[4]
            else:
                col = Card.COLORS[5]
        
        rect = [self.pos[0]-Card.WIDTH/2, self.pos[1]-Card.HEIGHT/2, Card.WIDTH, Card.HEIGHT]
        
        if self.rot % 180 == 90:
            rect = [self.pos[0]-Card.HEIGHT/2, self.pos[1]-Card.WIDTH/2, Card.HEIGHT, Card.WIDTH]
        
        if self.highlighted:
            pygame.draw.rect(win, Card.HIGHLIGHT, rect, 10)
        
        pygame.draw.rect(win, col, rect)
        
        if self.flip:
            num = Game.font.render(str(self.num), True, (0,0,0))
            
            num = pygame.transform.rotate(num, -self.rot)
            
            win.blit(num, [self.pos[0]-num.get_width()/2, self.pos[1]-num.get_height()/2])
    
    def is_clicked(self, x, y):
        if self.removed:
            return False
        
        rect = [self.pos[0]-Card.WIDTH/2, self.pos[1]-Card.HEIGHT/2, Card.WIDTH, Card.HEIGHT]
        
        if self.rot % 180 == 90:
            rect = [self.pos[0]-Card.HEIGHT/2, self.pos[1]-Card.WIDTH/2, Card.HEIGHT, Card.WIDTH]
        
        return (rect[0] <= x < rect[0] + rect[2]) and (rect[1] <= y < rect[1] + rect[3])