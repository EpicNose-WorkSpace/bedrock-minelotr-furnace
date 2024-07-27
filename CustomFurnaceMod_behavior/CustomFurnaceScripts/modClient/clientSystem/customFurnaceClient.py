# -*- coding: utf-8 -*-
from ...modClient.clientSystem.customContainerClientSystem import CustomContainerClientSystem
from ...modCommon import modConfig
from mod_log import logger

class CustomFurnaceClientSystem(CustomContainerClientSystem):
    def __init__(self, namespace, name):
        super(CustomFurnaceClientSystem, self).__init__(namespace, name)

    # 监听引擎和服务端脚本事件
    def ListenEvent(self):
        super(CustomFurnaceClientSystem, self).ListenEvent()
        #监听这个enchantInfo改变了  服务端那边读取完附魔信息 然后通过这个事件告知客户端的组件 执行附魔属性显示控件的改变
        self.ListenForEvent(modConfig.ModName, modConfig.ServerSystemName, modConfig.OnEnchantInfoChangedEvent,
                            self, self.onEnchantInfoChangedShow)

    # 取消监听引擎和服务端脚本事件
    def UnListenEvent(self):
        super(CustomFurnaceClientSystem, self).UnListenEvent()
        self.UnListenForEvent(modConfig.ModName, modConfig.ServerSystemName, modConfig.OnEnchantInfoChangedEvent,
                            self, self.onEnchantInfoChangedShow)

    # 在清除该system的时候调用取消监听事件
    def Destroy(self):
        self.UnListenEvent()


    #作为customFurnaceClient中服务端事件的回调函数 在这里将uiNode中的属性更改掉 获取uiNode示例 然后直接根据传入的参数  执行一下
    def onEnchantInfoChangedShow(self,args):
        print "打印一下被改变的附魔信息"
        print args



        blockName = args["blockInfo"]["blockName"]
        uiData = modConfig.UI_DEFS.get(blockName)
        if not uiData:
            logger.error("%s Has No UIData!!!" % blockName)
        uiNode = self.mUIManager.getUINode(uiData)
        uiNode.onEnchantInfoUpdate(args)
        pass

