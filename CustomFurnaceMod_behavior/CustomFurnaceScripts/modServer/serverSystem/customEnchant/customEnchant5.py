
import mod.server.extraServerApi as serverApi

from enchantEffectBase import EnchantEffectBase


class CustomEnchant5(EnchantEffectBase):
    def __init__(self, system, playerId, enchantData):
        super(CustomEnchant5, self).__init__(system, playerId, enchantData)

    #重写tick函数，每次tick给玩家添加2s等级为1的饥饿效果
    def tick(self):
        comp = serverApi.GetEngineCompFactory().CreateEffect(self.playerId)
        comp.AddEffectToEntity("strength", 2, 1, True)