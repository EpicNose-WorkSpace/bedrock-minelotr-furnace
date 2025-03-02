# -*- coding: utf-8 -*-
#
import random

from ..serverManager.furnaceMgrGas import FurnaceManagerGas
from ...modCommon import modConfig
from ...modCommon import EnchantID2Desc
from ...modServer.serverFactory.furnaceManagerFactory import FurnaceManagerFactory
from ...modServer.serverSystem.customContainerServerSystem import CustomContainerServerSystem
from ...modCommon.modCommonUtils import itemUtils
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
from mod_log import logger

minecraftEnum = serverApi.GetMinecraftEnum()
compFactory = serverApi.GetEngineCompFactory()





class CustomFurnaceServerSystem(CustomContainerServerSystem):
    def __init__(self, namespace, name):
        super(CustomFurnaceServerSystem, self).__init__(namespace, name)
        # key: (x, y, z, dimension), value: furnaceManager
        self.mCustomFurnaceDict = {}
        # 初始化可以进行右键打开的容器列表
        self.mCustomContainer = modConfig.CUSTOM_CONTAINER_LIST
        self.oriEnchantsHere = EnchantID2Desc.oriEnchants
        self.modEnchantsHere = EnchantID2Desc.modEnchants
        self.enchantLevelHere = EnchantID2Desc.enchantLevel


    def IsEnchantBook(self,enchatbookItem):
        # logger.info("aaaaaaaaaaaaaaaaaaa "+enchatbookItem)
        if enchatbookItem == "minecraft:enchanted_book":
            return True
        else:
            return False

    def ListenEvent(self):
        super(CustomFurnaceServerSystem, self).ListenEvent()
        # 监听服务端引擎事件
        self.ListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerBlockEntityTickEvent,
                            self, self.OnBlockEntityTick)

        #监听客户端引擎事件
        self.ListenForEvent(modConfig.ModName, modConfig.ClientSystemName,modConfig.onForgeButtonClickDownClientEvent,self,self.onForgeButtonClicked)
    def UnListenEvent(self):
        super(CustomFurnaceServerSystem, self).UnListenEvent()
        self.UnListenForEvent(serverApi.GetEngineNamespace(), serverApi.GetEngineSystemName(), modConfig.ServerBlockEntityTickEvent,
                              self, self.OnBlockEntityTick)
        self.UnListenForEvent(modConfig.ModName, modConfig.ClientSystemName,modConfig.onForgeButtonClickDownClientEvent,self,self.onForgeButtonClicked)

    def GetCustomContainerItems(self, dimension, blockName, blockPos):
        # 覆写基类方法，获取自定义熔炉中blockEntityData中的数据
        items = {}
        blockEntityComp = compFactory.CreateBlockEntityData(self.mLevelId)
        blockEntityData = blockEntityComp.GetBlockEntityData(dimension, blockPos)
        if blockEntityData:
            for i in range(0, modConfig.FURNACE_SLOT_NUM_DICT.get(blockName, 0)):
                key = "{0}{1}".format(modConfig.FURNACE_SLOT_PREFIX, i)
                items[key] = blockEntityData[key]
        return items

    def ResetCustomContainer(self, dimension, blockName, blockPos):
        # 覆写基类方法，方块被摧毁时需要重置的数据在这里处理
        furnaceKey = (blockPos[0], blockPos[1], blockPos[2], dimension)
        if furnaceKey in self.mCustomFurnaceDict:
            del self.mCustomFurnaceDict[furnaceKey]

    def UpdateCustomContainer(self, playerId, blockPos, dimension):
        # 覆写基类方法，获取自定义熔炉状态，更新熔炉状态（此处不要更新熔炉内物品槽，会导致飞行动画错误）
        furnaceMgr = self.mCustomFurnaceDict.get((blockPos[0], blockPos[1], blockPos[2], dimension))
        if furnaceMgr:
            furnaceData = self.CreateEventData()
            furnaceData["blockName"] = furnaceMgr.GetBlockName()
            furnaceData["isLit"] = furnaceMgr.IsLit()
            furnaceData["litDuration"] = furnaceMgr.GetLitDuration()
            furnaceData["isCooking"] = furnaceMgr.IsCooking()
            # modConfig.get
            self.NotifyToClient(playerId, modConfig.OnCustomContainerChangedEvent, furnaceData)

    def OnBlockEntityTick(self, args):
        # 避免频繁输出，易造成卡顿
        blockName = args["blockName"]
        blockPos = (args["posX"], args["posY"], args["posZ"])
        dimension = args["dimension"]
        blockKey = (args["posX"], args["posY"], args["posZ"], args["dimension"])
        # 在这里进行实现自定义熔炉的tick逻辑
        if blockName in modConfig.CUSTOM_CONTAINER_LIST:
            # 第一次tick的时候需要从blockEntity获取数据，之后只有数据更新才需要获取blockEntity进行更新
            furnaceMgr = self.mCustomFurnaceDict.get(blockKey)
            if not furnaceMgr:
                furnaceMgr = FurnaceManagerFactory.GetFurnaceManager(blockName)
                blockEntityComp = compFactory.CreateBlockEntityData(self.mLevelId)
                blockEntityData = blockEntityComp.GetBlockEntityData(args["dimension"], (args["posX"], args["posY"], args["posZ"]))
                furnaceItems = []
                for i in range(0, modConfig.FURNACE_SLOT_NUM_DICT.get(blockName, 0)):
                    key = "{0}{1}".format(modConfig.FURNACE_SLOT_PREFIX, i)
                    furnaceItems.append(blockEntityData[key])
                furnaceMgr.UpdateBlockData(furnaceItems)
                self.mCustomFurnaceDict[blockKey] = furnaceMgr
            # tick 当需要更新数据或UI时进入下面流程
            if furnaceMgr.Tick():
                # 更新blockEntity数据
                blockEntityComp = compFactory.CreateBlockEntityData(self.mLevelId)
                blockEntityData = blockEntityComp.GetBlockEntityData(args["dimension"], (args["posX"], args["posY"], args["posZ"]))
                blockItems = furnaceMgr.GetBlockItems()
                for i in range(0, modConfig.FURNACE_SLOT_NUM_DICT.get(blockName, 0)):
                    key = "{0}{1}".format(modConfig.FURNACE_SLOT_PREFIX, i)
                    blockEntityData[key] = blockItems[i]
                if not self.mCurOpenedBlock:
                    return
                # 如果当前ui界面打开则通知客户端更新UI
                for playerId, blockInfo in self.mCurOpenedBlock.items():
                    if blockPos in blockInfo.values() and dimension in blockInfo.values():
                        furnaceData = self.CreateEventData()
                        furnaceData[modConfig.CUSTOM_CONTAINER_BAG] = {}
                        for i in range(0, modConfig.FURNACE_SLOT_NUM_DICT.get(blockName, 0)):
                            key = "{0}{1}".format(modConfig.FURNACE_SLOT_PREFIX, i)
                            furnaceData[modConfig.CUSTOM_CONTAINER_BAG][key] = blockItems[i]
                        furnaceData["blockName"] = blockName
                        furnaceData["isLit"] = furnaceMgr.IsLit()
                        furnaceData["litDuration"] = furnaceMgr.GetLitDuration()
                        furnaceData["isCooking"] = furnaceMgr.IsCooking()
                        self.NotifyToClient(playerId, modConfig.OnCustomContainerChangedEvent, furnaceData)
                        break

    def OnCustomContainerItemSwap(self, playerId, fromSlot, fromItem, toSlot, toItem):
        # 因为熔炉槽位名是str，背包槽位名是int所以做如下判断
        if isinstance(fromSlot, str) and isinstance(toSlot, str):
            # 不允许熔炉内部槽物物品交换
            return False
        # 熔炉槽和背包槽之间的交换
        if isinstance(fromSlot, str) or isinstance(toSlot, str):
            itemComp = compFactory.CreateItem(playerId)
            blockEntityComp = compFactory.CreateBlockEntityData(self.mLevelId)
            blockInfo = self.GetBlockInfoByPlayerId(playerId)
            if not blockInfo:
                logger.error("Get opened block key error!")
                return False
            blockPos = blockInfo.get("blockPos")
            dimension = blockInfo.get("dimension")
            blockKey = (blockPos[0], blockPos[1], blockPos[2], dimension)
            blockEntityData = blockEntityComp.GetBlockEntityData(blockInfo.get("dimension"), blockInfo.get("blockPos"))
            furnaceMgr = self.mCustomFurnaceDict.get(blockKey)
            # 如果其中一个槽不可放置则返回
            if not furnaceMgr.CanSet(fromSlot, toItem) or not furnaceMgr.CanSet(toSlot, fromItem):
                return False
            # 从熔炉取出物品到背包
            if isinstance(toSlot, int):
                if furnaceMgr.GetSlot(fromSlot) == 0:
                    # 从生成槽取出物品时，只能在目标槽位为空时才可以取出
                    if toItem and not itemUtils.IsSameItem(fromItem, toItem):
                        return False
                furnaceMgr.UpdateSlotData(fromSlot, toItem)
                blockEntityData[fromSlot] = toItem

                itemComp.SpawnItemToPlayerInv(fromItem, playerId, toSlot)
                #在这增加一个附魔的逻辑
                self.TryToEnchantAfterSwap(itemComp,playerId,furnaceMgr,fromSlot,toSlot)

            # 从背包放置物品到熔炉
            else:
                furnaceMgr.UpdateSlotData(toSlot, fromItem)
                blockEntityData[toSlot] = fromItem
                if toItem:
                    itemComp.SpawnItemToPlayerInv(toItem, playerId, fromSlot)
                else:
                    itemComp.SetInvItemNum(fromSlot, 0)
        return True






    def OnCustomContainerItemDrop(self, playerId, slot):
        blockEntityComp = compFactory.CreateBlockEntityData(self.mLevelId)
        blockInfo = self.GetBlockInfoByPlayerId(playerId)
        if not blockInfo:
            logger.error("Get opened block key error!")
            return False
        blockPos = blockInfo.get("blockPos")
        dimension = blockInfo.get("dimension")
        blockKey = (blockPos[0], blockPos[1], blockPos[2], dimension)
        blockEntityData = blockEntityComp.GetBlockEntityData(blockInfo.get("dimension"), blockInfo.get("blockPos"))
        furnaceMgr = self.mCustomFurnaceDict.get(blockKey)
        furnaceMgr.UpdateSlotData(slot, None)
        blockEntityData[slot] = None
        return True






    #这里要注册个事件 监听客户端按下按钮
    # def TryToEnchantAfterSwap(self,playerId,furnaceMgr,fromItem,toSlot):
    #     if self.IsEnchantBook(furnaceMgr.mItems[3].get("itemName")):
    #         comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    #         comp.AddModEnchantToInvItem(toSlot, "utmha:lotrenchant_move_speed", 1)
    #     return True

    def onForgeButtonClicked(self,args):
        # print "服务端已接受拉 下面罗列一下过来的参数"
        # print args
        print "运行4"
        if self.mCurOpenedBlock[args.get("playerId")]:
            blockInfo=self.mCurOpenedBlock[args.get("playerId")]
            blockName=self.mCurOpenedBlock[args.get("playerId")].get("blockName")
            blockPos = blockInfo.get("blockPos")
            dimension = blockInfo.get("dimension")
            blockKey = (blockPos[0], blockPos[1], blockPos[2], dimension)
            print "运行3"
            if self.mCustomFurnaceDict.get(blockKey):
                furnaceMgr = self.mCustomFurnaceDict.get(blockKey)
                print "运行2"

                #这里不看2号结果位是否有东西了 单纯执行存储附魔信息的操作
                if furnaceMgr.mItems[3] is not None:
                    if self.IsEnchantBook(furnaceMgr.mItems[3].get("itemName")):
                        print "附魔书信息"
                        print furnaceMgr.mItems[3]
                        # 进入原版附魔环节
                        if furnaceMgr.mItems[3].get("enchantData") is not None:   #自定义附魔 和 原版附魔可能同时存在于一本书上 所以这俩循环都要执行
                            vanillaEnchants = []
                            for enchant in furnaceMgr.mItems[3].get("enchantData"): #从附魔书中取出一个数组 以字典形式存入mEnchantInfo
                                id,lvl = enchant
                                vanillaEnchants.append({'id': id, 'lvl': lvl})

                            furnaceMgr.mEnchantInfo = vanillaEnchants
                            print "打印一下mEnchantInfo"
                            print furnaceMgr.mEnchantInfo



                        # 进入自定义附魔环节
                        if furnaceMgr.mItems[3].get("modEnchantData") is not None:
                            # print "a"
                            modEnchants = []
                            for modenchant in furnaceMgr.mItems[3].get("modEnchantData"):
                                id,lvl = modenchant
                                modEnchants.append({'id': id,'lvl': lvl })
                            furnaceMgr.mModEnchantInfo = modEnchants
                            print "打印一下modEnchantInfo"
                            print furnaceMgr.mModEnchantInfo

                        enchantInfoEventData = self.CreateEventData()
                        enchantInfoEventData["enchantData"]=furnaceMgr.mEnchantInfo
                        enchantInfoEventData["modEnchantData"]=furnaceMgr.mModEnchantInfo
                        # enchantInfoEventData["blockName"]=blockName
                        enchantInfoEventData["blockInfo"]=blockInfo #用于screenNode中识别哪一个方块
                        enchantInfoEventData["levelId"]=self.mLevelId
                        self.GetChineseEnchantName(enchantInfoEventData)
                        self.NotifyToClient(args.get("playerId"),modConfig.OnEnchantInfoChangedEvent,enchantInfoEventData)
                        # comp = serverApi.GetEngineCompFactory().CreateItem(args.get("playerId"))
                        # comp.AddModEnchantToInvItem(0, "utmha:lotrenchant_move_speed", 1)
                        print "运行1"
                    return True



        pass

    def GetChineseEnchantName(self,args):
        comp = serverApi.GetEngineCompFactory().CreateGame(self.mLevelId)
        # args["enchantNames"]=
            # comp.GetChinese("entity.wolf.name")
        # comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        str2Show = ""
        for orienchant in args["enchantData"]:
            # strid = self.oriEnchantsHere.get(orienchant["id"])
            strid= comp.GetChinese(str(self.oriEnchantsHere.get(orienchant["id"])))
            # print strid
            strlvl=self.enchantLevelHere.get(orienchant["lvl"])
            str2Show = str2Show+strid+strlvl
            # str2Show += EnchantID2Desc.enchantLevel.get(orienchant["lvl"])
        # print str(self.mModEnchantInfo)
        for modenchant in args["modEnchantData"]:
            # print modenchant
            # strid = self.modEnchantsHere.get(str(modenchant["id"]).replace(":", "_"))
            strid = self.comp.GetChinese(str(self.modEnchantsHere.get(str(modenchant["id"]).replace(":","_"))))
            strlvl = self.enchantLevelHere.get(modenchant["lvl"])
            str2Show = str2Show+strid+strlvl
            # str2Show =str2Show+self.modEnchantsHere.get(str(modenchant["id"]).replace(":","_"))+self.enchantLevelHere.get(modenchant["lvl"])
            # str2Show += EnchantID2Desc.enchantLevel.get(orienchant["lvl"])
        args["enchantNames"] = str2Show


    # def TryToEnchantAfterSwap(self,args):
    #     print "运行4"
    #     if self.mCurOpenedBlock[args.get("playerId")]:
    #         blockInfo=self.mCurOpenedBlock[args.get("playerId")]
    #         blockPos = blockInfo.get("blockPos")
    #         dimension = blockInfo.get("dimension")
    #         blockKey = (blockPos[0], blockPos[1], blockPos[2], dimension)
    #         print "运行3"
    #         if self.mCustomFurnaceDict.get(blockKey):
    #             furnaceMgr = self.mCustomFurnaceDict.get(blockKey)
    #             print "运行2"
    #             if (furnaceMgr.mItems[3] is not None) & (furnaceMgr.mItems[0] is not None):
    #                 if self.IsEnchantBook(furnaceMgr.mItems[3].get("itemName")):
    #                     comp = serverApi.GetEngineCompFactory().CreateItem(args.get("playerId"))
    #                     comp.AddModEnchantToInvItem(0, "utmha:lotrenchant_move_speed", 1)
    #                     print "运行1"
    #                 return True


    def TryToEnchantAfterSwap(self,itemComp,playerId,furnaceMgr,fromSlot,toSlot):
        print "交换附魔运行4"
        # print
        if furnaceMgr.mItems[3] is not None:
            print "交换附魔运行6"
            if self.IsEnchantBook(furnaceMgr.mItems[3].get("itemName")):
                print "交换附魔运行7"
                # furnaceMgr.GetSlot(fromSlot) == 0
                if furnaceMgr.GetSlot(fromSlot) == 0 or furnaceMgr.GetSlot(fromSlot) == 2:
                # if (furnaceMgr.mItems[2] is not None) or (furnaceMgr.mItems[0] is not None):
                    print "交换附魔运行5"
                    # comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
                    # self.mEnchantInfo = []  # [(1,2),(2,3)]
                    # self.mModEnchantInfo = []  # [{"enchantName":"","enchantLvl":2}]
                    if furnaceMgr.mEnchantInfo:
                        print "交换附魔运行2"
                        for enchant in furnaceMgr.mEnchantInfo:
                            print "附魔之前打印一下参数"
                            print furnaceMgr.mEnchantInfo
                            # print id2,lvl2
                            itemComp.AddEnchantToInvItem(toSlot, enchant["id"], enchant["lvl"])
                    if furnaceMgr.mModEnchantInfo:
                        print "交换附魔运行3"
                        for enchant2 in furnaceMgr.mModEnchantInfo:
                            print "附魔之前打印一下参数"
                            print furnaceMgr.mModEnchantInfo
                            # print id3,lvl3
                            itemComp.AddModEnchantToInvItem(toSlot, enchant2["id"], enchant2["lvl"])
                    # comp.AddModEnchantToInvItem(0, "utmha:lotrenchant_move_speed", 1)
                    print "交换附魔运行1"
                    return True




