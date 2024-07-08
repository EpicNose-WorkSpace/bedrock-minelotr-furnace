# -*- coding: utf-8 -*-

# 获取引擎服务端API的模块
import mod.server.extraServerApi as serverApi

from customEnchant5 import CustomEnchant5
# 获取引擎服务端System的基类，System都要继承于ServerSystem来调用相关函数
# from customEnchant1 import CustomEnchant1
# from customEnchant2 import CustomEnchant2
# from customEnchant3 import CustomEnchant3
# from customEnchant5 import CustomEnchant5

ServerSystem = serverApi.GetServerSystemCls()

#附魔效果与实现类的对应表
ENCHANT_EFFECT_MAP = {
    # "demoenchant:customenchant1": CustomEnchant1, #疾行
    # "demoenchant:customenchant2": CustomEnchant2, #雷鸣四方
    # "demoenchant:customenchant3": CustomEnchant3, #战利品
    # "demoenchant:customenchant4": CustomEnchant4,  #沉重
    "utmha:lotrenchant_move_speed": CustomEnchant5  #血性
}

#穿戴生效附魔列表
ARMOR_ENCHANT = [
    # "demoenchant:customenchant1",
    # "demoenchant:customenchant2"
]

# 在modMain中注册的Server System类
class EnchantTestServerSystem(ServerSystem):

    def __init__(self, namespace, systemName):
        super(EnchantTestServerSystem, self).__init__(namespace, systemName)

        #玩家已经获得附魔效果
        #self.activeEnchant表结构如下:
        #{playerId1 : {enchantKey1 : enchant1, enchantKey2 : enchant2 }, playerId2 = {enchantKey1 : enchant3, enchantKey2 : enchant4 }, ...}
        self.activeEnchant = {}

        #开启定时器，每秒对附魔对象进行tick，方便实现循环类型附魔效果
        comp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
        comp.AddRepeatedTimer(1.0, self.EnchantTick)

        #监听事件
        self.ListenEvent()

    def ListenEvent(self):
        #监听穿着装备变化事件，用于实现穿着类型附魔效果
        self.ListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(), "OnNewArmorExchangeServerEvent", self, self.NewArmorExchange)
        #监听主手道具变化事件，用于实现手持类型附魔效果
        self.ListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(), "OnCarriedNewItemChangedServerEvent", self, self.CarriedNewItemChange)
        #监听附魔台物品放到附魔台上，修改附魔选项值
        self.ListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(), "OnItemPutInEnchantingModelServerEvent", self, self.ItemPutInEnchantModel)

    def UnListenEvent(self):
        self.UnListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(),"OnNewArmorExchangeServerEvent", self, self.NewArmorExchange)
        self.UnListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(),"OnCarriedNewItemChangedServerEvent", self, self.CarriedNewItemChange)
        self.UnListenForEvent(serverApi.GetEngineNamespace(),serverApi.GetEngineSystemName(),"OnItemPutInEnchantingModelServerEvent", self, self.ItemPutInEnchantModel)


    #主手武器切换执行操作
    def CarriedNewItemChange(self, args):
        playerId = args["playerId"]
        oldItemDict = args["oldItemDict"]
        newItemDict = args["newItemDict"]
        #移除替换下装备的附魔效果
        self.removeEnchantEffect(playerId, oldItemDict)
        #添加替换上装备的附魔效果
        self.addEnchantEffect(playerId, newItemDict)

    #穿着装备切换执行操作
    def NewArmorExchange(self, args):
        playerId = args["playerId"]
        oldItemDict = args["oldArmorDict"]
        newItemDict = args["newArmorDict"]

        #移除切换前装备的附魔效果
        self.removeEnchantEffect(playerId, oldItemDict, True)
        #添加切换后装备的附魔效果
        self.addEnchantEffect(playerId, newItemDict, True)

    #移除附魔效果
    def removeEnchantEffect(self, playerId, oldItemDict, isArmorChange = False):
        #如果此玩家没有使用过自定义附魔(self.activeEnchant中没有此player的信息)，则直接返回
        if not self.activeEnchant.get(playerId):
            return

        if not oldItemDict:
            return

        #如果道具为附魔书则不作逻辑处理
        if oldItemDict["newItemName"] == "minecraft:enchanted_book":
            return

        #如果自定义附魔类别为空则不作逻辑处理
        modEnchantDatas = oldItemDict["modEnchantData"]
        if len(modEnchantDatas) <= 0:
            return

        #遍历玩家身上的附魔效果，如果有则进行移除
        for enchantData in modEnchantDatas:
            enchantIdentifier = enchantData[0]
            #从self.activeEnchant找到匹配玩家，拿到该玩家身上的附魔属性
            playerEnchant = self.activeEnchant.get(playerId)
            enchant = playerEnchant.get(enchantIdentifier)
            if enchant:
                #判断是否是穿戴类型附魔，穿戴类型附魔只能通过OnNewArmorExchangeServerEvent驱动
                if enchant.isArmorEnchant() != isArmorChange:
                    continue
                #执行附魔效果退出函数，删除效果，反监听事件等
                enchant.onExit()
                del playerEnchant[enchantIdentifier]

    #添加附魔效果
    def addEnchantEffect(self, playerId, newItemDict, isArmorChange = False):
        if not newItemDict:
            return

        #如果道具为附魔书则不作逻辑处理
        if newItemDict["newItemName"] == "minecraft:enchanted_book":
            return

        #如果自定义附魔类别为空则不作逻辑处理
        modEnchantDatas = newItemDict["modEnchantData"]
        if len(modEnchantDatas) <= 0:
            return

        #检测self.activeEnchant中是否有相关玩家的附魔属性表，如果没有则创建
        if not self.activeEnchant.get(playerId):
            self.activeEnchant[playerId] = {}

        #遍历自定义附魔信息，并为玩家添加相应效果
        for enchantData in modEnchantDatas:
            enchantIdentifier = enchantData[0]
            enchantEffectCls = ENCHANT_EFFECT_MAP.get(enchantIdentifier)
            if enchantEffectCls:
                enchant =  enchantEffectCls(self, playerId, enchantData)
                #判断是否是穿戴类型附魔，穿戴类型附魔只能通过OnNewArmorExchangeServerEvent驱动
                if enchant.isArmorEnchant() != isArmorChange:
                    continue
                #执行附魔效果进入函数，添加效果，监听事件等
                enchant.onEnter()
                playerEnchant = self.activeEnchant[playerId]
                playerEnchant[enchantIdentifier] = enchant


    def EnchantTick(self):
        #每秒对玩家身上的附魔效果对象进行tick，方便实现循环类型附魔，可看customEnchant2.py
        for _, playerId in enumerate(self.activeEnchant):
            for _, enchant in self.activeEnchant[playerId].iteritems():
                enchant.tick()


    #附魔台上附魔物品发生变化触发
    def ItemPutInEnchantModel(self, args):
        slotType = args["slotType"]

        if slotType != serverApi.GetMinecraftEnum().EnchantSlotType.ARMOR_HEAD:
            return

        #如果附魔物品是头盔，则将其附魔选项替换为雷鸣四方
        # args["change"] = True
        # args["options"] = [
        #     {'enchantData': [], 'modEnchantData': [("demoenchant:customenchant2", 1)], 'cost': 2},
        #     {'enchantData': [], 'modEnchantData': [("demoenchant:customenchant2", 2)], 'cost': 4},
        #     {'enchantData': [], 'modEnchantData': [("demoenchant:customenchant2", 3)], 'cost': 6}
        # ]
