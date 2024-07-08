# -*- coding: utf-8 -*-

#附魔效果基类，主要进行一些简单赋值操作
class EnchantEffectBase(object):
    def __init__(self, mSystem, playerId, enchantData):
        self.mSystem = mSystem
        self.playerId = playerId
        self.enchantData = enchantData

    def onEnter(self):
        pass

    def tick(self):
        pass

    def onExit(self):
        pass

    def isArmorEnchant(self):
        return False
