# -*- coding:utf-8 -*-
from ...modCommon.modCommonMgr.furnaceRecipeMgr import FurnaceRecipeManager
from ...modCommon import modConfig
from ...modCommon.modCommonMgr.furnaceMgrBase import FurnaceManagerBase
from ...modCommon.modCommonUtils import itemUtils
from mod_log import logger
import mod.server.extraServerApi as serverApi
# from ...modServer.serverSystem.customFurnaceServer import CustomFurnaceServerSystem
class FurnaceManagerGas(FurnaceManagerBase):
    """继承自FurnaceManagerBase基类，在这里可以覆写CanBurn函数和Burn函数来实现不同烧炼逻辑"""
    def __init__(self):
        super(FurnaceManagerGas, self).__init__()
        self.mRecipeMgr = FurnaceRecipeManager()
        self.mBlockName = "customblocks:custom_furnace"

    def CanBurn(self):
        """判断是否能够烧炼，只有当生成槽没物品或者生成物跟生成槽物品一致且生成槽物品小于最大堆叠数才返回True"""
        if not self.mItems[2]:
            return False
        resultItem = self.mRecipeMgr.GetFurnaceResult(self.mItems[2].get("itemName"))
        # 配方中没有匹配的生成物返回False
        if not resultItem:
            return False
        # 生成槽为空返回True
        if not self.mItems[0]:
            return True
        # 生成物与生成槽中物品不是同一个物品返回False
        if not itemUtils.IsSameItem(self.mItems[0], resultItem):
            return False
        # 生成槽中物品与生成物一致且堆叠数小于最大堆叠数返回True，最大堆叠数在配方中配置，默认为64
        if self.mItems[0].get("count") < resultItem.get("maxStackSize", modConfig.MAX_STACK_SIZE):
            return True
        return False

    def Burn(self):
        """烧炼过程，消耗原料生成烧炼物"""
        if not self.CanBurn():

            return
        resultItem = self.mRecipeMgr.GetFurnaceResult(self.mItems[2].get("itemName"))
        if not self.mItems[0]:
            self.mItems[0] = resultItem
            self.mItems[0]["count"] = 1
        else:
            self.mItems[0]["count"] += 1
        self.mItems[2]["count"] -= 1
        if self.mItems[2]["count"] == 0:
            self.mItems[2] = None

    def CanSet(self, slotName, item):
        slot = self.GetSlot(slotName)
        # 如果为背包槽允许放置
        if slot == -1:
            return True
        # 如果为生成槽禁止放置
        if slot == 0:
            if item:
                return False
            return True
        # 如果为燃料槽需是燃料才可以放置
        if slot == 1:
            if item and not self.mRecipeMgr.IsFuelItem(item["itemName"]):
                return False
            return True
        # 如果为原料槽可放置
        if slot == 2:
            return True
        if slot == 3:
            if item and not self.IsEnchatBook(item["itemName"]):
                return False
            return True
        return False

    #用于判断第四格是不是附魔书
    def IsEnchatBook(self, enchatbookItem):
        # logger.info("aaaaaaaaaaaaaaaaaaa "+enchatbookItem)
        if enchatbookItem == "minecraft:enchanted_book":
            return True
        return False

    def TryEnchant(self):
        # comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        # comp.AddModEnchantToInvItem(0, "customenchant", 2)
        pass



    # def UseEnchantBook(self):  #在不烧的时候执行
    #     if self.mItems[3] and self.mItems[2] and (not self.mItems[1]):
    #         key_found = None
    #         for key, value in CustomFurnaceServerSystem.mCurOpenedBlock.items():
    #             if value == self:
    #                 key_found = key
    #                 break
    #         if key_found is not None:
    #             blockPos = key_found[:3]
    #             dimension = key_found[-1]
    #             for playerId, blockInfo in CustomContainerServerSystem.mCurOpenedBlock.items():
    #                 if blockPos in blockInfo.values() and dimension in blockInfo.values():
    #                     comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    #                     comp.AddModEnchantToInvItem(0, "utmha:lotrenchant_move_speed", 1)
    #                     break
    #     return True
