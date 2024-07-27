# -*- coding: utf-8 -*-
from mod.client.ui.viewBinder import ViewBinder
from mod_log import logger

from ..clientUtils import apiUtil
from ...modCommon import modConfig
from ...modClient.ui.customContainerUIBase import CustomContainerUIScreenBase
import mod.client.extraClientApi as clientApi

class CustomFurnaceUIScreen(CustomContainerUIScreenBase):

    def __init__(self, namespace, name, param):
        super(CustomFurnaceUIScreen, self).__init__(namespace, name, param)
        self.mFireMaskPath = self.mRightPanelPath + "/fire/fireMask"
        self.mArrowMaskPath = self.mRightPanelPath + "/arrow/arrowMask"
        self.mForgeButtonPath = self.mRightPanelPath+"/forgeBtn"
        # 管理燃烧状态相关数据
        self.mIsLit = False
        self.mIsCooking = False
        self.mLitProgress = 0
        self.mLitDuration = 0
        self.mBurnProgress = 0
        self.mEnchantInfo = []
        self.mModEnchantInfo = []

    def Update(self):
        # 执行父类方法
        super(CustomFurnaceUIScreen, self).Update()
        # 更新燃烧动画
        if not self.mIsLit:
            self.mLitProgress = 0
            self.SetSpriteClipRatio(self.mFireMaskPath, 1)
        else:
            # 更新火焰进度
            self.mLitProgress += 1
            fireRatio = (self.mLitProgress * 2.0) / (self.mLitDuration * 3.0)
            self.SetSpriteClipRatio(self.mFireMaskPath, fireRatio)
            if fireRatio == 1:
                self.mLitProgress = 0
        if not self.mIsCooking:
            self.mBurnProgress = 0
            self.SetSpriteClipRatio(self.mArrowMaskPath, 1)
        else:
            # 更新箭头进度
            self.mBurnProgress += 1
            arrowRatio = self.mBurnProgress / (modConfig.BURN_INTERVAL * 30.0)
            self.SetSpriteClipRatio(self.mArrowMaskPath, 1.0 - arrowRatio)
            if arrowRatio == 1:
                self.mBurnProgress = 0

    def InitCustomContainerUI(self, args):
        items = args[modConfig.CUSTOM_CONTAINER_BAG]
        for slotName, itemDict in items.items():
            slotPath = "{0}/{1}".format(self.mRightPanelPath, slotName)
            self.mBagInfo[slotPath] = {"slot": slotName, "item": itemDict}
            self.mSlotToPath[slotName] = slotPath
            self.SetSlotUI(slotPath, itemDict)
        # 初始化燃烧进度
        self.SetSpriteClipRatio(self.mFireMaskPath, 1)
        self.SetSpriteClipRatio(self.mArrowMaskPath, 1)

    def UpdateCustomContainerUI(self, args):
        for key, value in args.items():
            # 更新燃烧状态
            if key == "isLit":
                self.mIsLit = value
            # 更新燃料数据
            elif key == "litDuration":
                if value != self.mLitDuration:
                    self.mLitDuration = args["litDuration"]
                    self.mLitProgress = 0
            elif key == "isCooking":
                self.mIsCooking = value
            # 更新熔炉槽物品信息
            elif key == modConfig.CUSTOM_CONTAINER_BAG:
                for itemSlot, itemDict in value.items():
                    slotPath = "{0}/{1}".format(self.mRightPanelPath, itemSlot)
                    self.mBagInfo[slotPath] = {"slot": itemSlot, "item": itemDict}
                    self.SetSlotUI(slotPath, itemDict)

    def UpdateBagUI(self, args):
        # print "参数参数"
        # print args
        # print "参数参数"

        super(CustomFurnaceUIScreen, self).UpdateBagUI(args)

        self.RegisterForgeButton()



    #增加自己自定义的按钮注册
    def RegisterForgeButton(self):
        # super(CustomFurnaceUIScreen, self).RegisterButtonEvents()
        # self.AddTouchEventHandler(self.mDropAreaPath, self.onForgeButtonClick, {"isSwallow": True})
        # print "锻造按钮路径"
        # print self.mForgeButtonPath
        # print "锻造按钮路径"
        # buttonUIControl = self.GetBaseUIControl(self.mForgeButtonPath).asButton()
        self.GetBaseUIControl(self.mForgeButtonPath).asButton().AddTouchEventParams({"isSwallow": True})
        self.GetBaseUIControl(self.mForgeButtonPath).asButton().SetButtonTouchDownCallback(self.onForgeButtonClick)
        # buttonUIControl.AddTouchEventParams({"isSwallow": True})
        # buttonUIControl.SetButtonTouchDownCallback(self.onForgeButtonClick)
        print "按下回调注册"

    #这个绑定似乎是按tick执行的 一秒贼多次
    @ViewBinder.binding(ViewBinder.BF_BindString, "#enchantName")
    def showEnchantName(self):


        print str(self.mEnchantInfo)

        return str(self.mEnchantInfo)
        # print "打印一下ui内部函数传过来的附魔信息"
        # print args["mEnchantInfo"]
        # pass
        # print args
        # return str(self.mModEnchantInfo)

    @ViewBinder.binding(ViewBinder.BF_ButtonClickDown)
    def forgeButton(self, args):
        print "执行数据绑定函数"


    #     # 参数args含有按钮的信息，可以尝试打印来查看
    #     # 多个按钮也可以使用同一个函数，args中的路径可以用于判断你按下了哪个按钮
    #     # 已经在json中填写"bindings"为集合的按钮，拥有额外的参数：所在集合名和序数，你也可以通过打印查看他们的路径，其控件名为 控件库控件名+index，其路径就在gird之下
    #
    #     # self.times += 1
    #     # if self.times > maxInt:
    #     #     self.times = 0
    #     # self.TestDict = List[self.times]

    def onForgeButtonClick(self,args):
        eventData = apiUtil.GetModClientSystem().CreateEventData()
        eventData["playerId"] = apiUtil.GetModClientSystem().GetPlayerId()
        apiUtil.GetModClientSystem().NotifyToServer(modConfig.onForgeButtonClickDownClientEvent, eventData)
        print "已发送锻造按钮点击事件"
        # touchEventEnum = clientApi.GetMinecraftEnum().TouchEvent
        # touchEvent = args["TouchEvent"]
        # if touchEvent == touchEventEnum.TouchDown:
        #     self.mContainerStateMachine.ReceiveEvent(args["ButtonPath"], ButtonEventType.Clicked)

        # pass

    def onEnchantInfoUpdate(self,args):
        # 这个方法拿来执行附魔数据更新 由furnaceClientSys 调用
        self.mModEnchantInfo = args["mModEnchantInfo"]
        self.mEnchantInfo = args["mEnchantInfo"]
        print "成功进入到ui中的方法"
        # self.testtest()testtest(args)
        # self.testtest(args)
        # self.showEnchantName(args)
        # self.showEnchantName()
        pass

    # def testtest(self,args):
    #     print "testtest"
    #     print args

