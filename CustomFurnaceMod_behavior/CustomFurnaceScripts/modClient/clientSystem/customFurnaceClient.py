# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
from ...modClient.clientSystem.customContainerClientSystem import CustomContainerClientSystem
from ...modCommon import modConfig
from mod_log import logger

class CustomFurnaceClientSystem(CustomContainerClientSystem):
    def __init__(self, namespace, name):
        super(CustomFurnaceClientSystem, self).__init__(namespace, name)
        # key: (x, y, z, dimension), value: enchantData+modEnchantData
        self.pos2enchantData = {}

    # 监听引擎和服务端脚本事件
    def ListenEvent(self):
        super(CustomFurnaceClientSystem, self).ListenEvent()
        #监听这个enchantInfo改变了  服务端那边读取完附魔信息 然后通过这个事件告知客户端的组件 执行附魔属性显示控件的改变
        self.ListenForEvent(modConfig.ModName, modConfig.ServerSystemName, modConfig.OnEnchantInfoChangedEvent,
                            self, self.onEnchantInfoChangedShow)
        # self.ListenForEvent(modConfig.ModName, modConfig.ClientSystemName,
        #                     modConfig.onCloseButtonClickedClientEvent, self, self.OnCustomContainerUIClose)
        # self.ListenForEvent(modConfig.ModName, clientApi.GetEngineSystemName(), modConfig.onCloseButtonClickedClientEvent,
        #                     self, self.OnCustomContainerUIClose)



    # 取消监听引擎和服务端脚本事件
    def UnListenEvent(self):
        super(CustomFurnaceClientSystem, self).UnListenEvent()
        self.UnListenForEvent(modConfig.ModName, modConfig.ServerSystemName, modConfig.OnEnchantInfoChangedEvent,
                            self, self.onEnchantInfoChangedShow)
        # self.UnListenForEvent(clientApi.GetEngineNamespace(), clientApi.GetEngineSystemName(),
        #                     modConfig.onCloseButtonClickedClientEvent, self, self.OnCustomContainerUIClose)
        # self.UnListenForEvent(modConfig.ModName, clientApi.GetEngineSystemName(), modConfig.onCloseButtonClickedClientEvent,
        #                     self, self.OnCustomContainerUIClose)

    # 在清除该system的时候调用取消监听事件
    def Destroy(self):
        self.UnListenEvent()

    def OpenCustomContainer(self, args):   #打开自定义容器界面的回调函数 这里覆写一下 然后需要在这里记录下对应的enchantData
        super(CustomFurnaceClientSystem,self).OpenCustomContainer(args)

        blockName = args["blockName"]
        uiData = modConfig.UI_DEFS.get(blockName)
        if not uiData:
            logger.error("%s Has No UIData!!!" % blockName)
        uiNode = self.mUIManager.getUINode(uiData)

        # if self.pos2enchantData.get
        if self.pos2enchantData.has_key((args["blockPos"],args["dimension"])):
            print "打开界面发现还有数据 直接沿用"
            uiNode.onEnchantInfoUpdate(self.pos2enchantData.get((args["blockPos"],args["dimension"])))

        print "打印一下打开自定义容器时的数据"
        print args

    # def OnCustomContainerUIClose(self, args): #在关闭界面后 清掉这个screenNode的附魔数据 以免传染到别的自定义熔炉方块（打开别的发现还是显示着原来的附魔数据）
    #     #
    #     # super(CustomFurnaceClientSystem, self).OnCustomContainerUIClose(args)
    #     blockName = args["blockName"]
    #     uiData = modConfig.UI_DEFS.get(blockName)
    #     if not uiData:
    #         logger.error("%s Has No UIData!!!" % blockName)
    #     uiNode = self.mUIManager.getUINode(uiData)
    #
    #     print "执行关闭 打印一下数据"
    #     print args
    #
    #     if self.pos2enchantData.has_key((args["blockPos"], args["dimension"])):
    #         uiNode.mEnchantInfo = []
    #         uiNode.mModEnchantInfo = []
    #         print "关闭后清空界面的附魔数据"
            # uiNode.

    #作为customFurnaceClient中服务端事件的回调函数 在这里将uiNode中的属性更改掉 获取uiNode示例 然后直接根据传入的参数  执行一下
    def onEnchantInfoChangedShow(self,args):
        print "打印一下被改变的附魔信息"
        print args
        key = (args["blockInfo"]["blockPos"], args["blockInfo"]["dimension"])
        # value = {"allEnchantData": {"enchantData": args["enchantData"], "modEnchantData": args["modEnchantData"]}}
        value = {"enchantData": args["enchantData"], "modEnchantData": args["modEnchantData"]}
        self.pos2enchantData.update({key: value})



        blockName = args["blockInfo"]["blockName"]
        uiData = modConfig.UI_DEFS.get(blockName)
        if not uiData:
            logger.error("%s Has No UIData!!!" % blockName)
        uiNode = self.mUIManager.getUINode(uiData)
        uiNode.onEnchantInfoUpdate(args)
        pass

