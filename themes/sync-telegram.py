#!/usr/bin/python3
import os, shutil, zipfile

HOME = os.path.expanduser("~")
CFG_DIR = os.path.join(HOME, ".config/cyberdeck")
os.makedirs(CFG_DIR, exist_ok=True)

TG_COLORS = """// Studio Matte-Grey Theme for Telegram Desktop
windowBg: #121316;
windowFg: #e6e9ef;
windowBgOver: #1c1f25;
windowBgRipple: #262a32;
windowFgOver: #ffffff;
windowSubTextFg: #828894;
windowSubTextFgOver: #9ea4b0;
windowBoldFg: #e6e9ef;
windowBoldFgOver: #ffffff;
windowBgActive: #5c626d;
windowFgActive: #ffffff;
windowActiveTextFg: #b0b6c0;
windowShadowFg: #00000088;

titleBg: #14161a;
titleBgActive: #14161a;
titleButtonBg: #14161a;
titleButtonFg: #9ea4b0;
titleButtonBgOver: #22252c;
titleButtonFgOver: #ffffff;
titleButtonCloseBgOver: #4a2c30;
titleButtonCloseFgOver: #ffffff;
titleFgActive: #e6e9ef;
titleFg: #7a818e;

dialogsBg: #14161a;
dialogsNameFg: #e6e9ef;
dialogsChatIconFg: #9ea4b0;
dialogsDateFg: #7a818e;
dialogsTextFg: #9ea4b0;
dialogsTextFgService: #b0b6c0;
dialogsDraftFg: #a38f8f;
dialogsVerifiedIconBg: #6c727d;
dialogsVerifiedIconFg: #121316;
dialogsSendingIconFg: #7a818e;
dialogsSentIconFg: #9ea4b0;
dialogsUnreadBg: #5c626d;
dialogsUnreadBgMuted: #32363f;
dialogsUnreadFg: #ffffff;
dialogsBgOver: #1b1e24;
dialogsNameFgOver: #ffffff;
dialogsDateFgOver: #9ea4b0;
dialogsTextFgOver: #c8ccd2;
dialogsBgActive: #262a33;
dialogsNameFgActive: #ffffff;
dialogsChatIconFgActive: #ffffff;
dialogsDateFgActive: #d4d8de;
dialogsTextFgActive: #e6e9ef;
dialogsTextFgServiceActive: #ffffff;
dialogsUnreadBgActive: #8c939e;
dialogsUnreadFgActive: #121316;

searchedBarBg: #16181c;
searchedBarFg: #9ea4b0;

topBarBg: #15171b;
emojiPanBg: #16181c;
emojiPanCategories: #14161a;
emojiPanHeaderFg: #9ea4b0;

historyComposeAreaBg: #16181c;
historyComposeAreaFg: #e6e9ef;
historyComposeAreaFgService: #828894;
historyComposeIconFg: #828894;
historyComposeIconFgOver: #d4d8de;
historySendIconFg: #b0b6c0;
historySendIconFgOver: #ffffff;
historyPinnedBg: #16181c;
historyReplyBg: #16181c;
historyReplyIconFg: #9ea4b0;
historyReplyCancelFg: #828894;
historyReplyCancelFgOver: #e6e9ef;

msgInBg: #1a1d23;
msgInBgSelected: #252932;
msgOutBg: #242831;
msgOutBgSelected: #303540;
msgSelectOverlay: #5c626d44;
msgStickerOverlay: #5c626d66;
msgInServiceFg: #b0b6c0;
msgInServiceFgSelected: #ffffff;
msgOutServiceFg: #c8ccd2;
msgOutServiceFgSelected: #ffffff;
msgInShadow: #00000000;
msgOutShadow: #00000000;
msgInDateFg: #7a818e;
msgInDateFgSelected: #9ea4b0;
msgOutDateFg: #8c939e;
msgOutDateFgSelected: #b0b6c0;
msgServiceFg: #d4d8de;
msgServiceBg: #1c1f26cc;
msgServiceBgSelected: #282c35cc;
msgInReplyBarColor: #7a818e;
msgInReplyBarSelColor: #9ea4b0;
msgOutReplyBarColor: #9ea4b0;
msgOutReplyBarSelColor: #c8ccd2;
msgInMonoFg: #b0b6c0;
msgOutMonoFg: #c8ccd2;

 historyTextInFg: #e6e9ef;
historyTextInFgSelected: #ffffff;
historyTextOutFg: #e6e9ef;
historyTextOutFgSelected: #ffffff;
historyLinkInFg: #b0b6c0;
historyLinkOutFg: #c8ccd2;
historyFileNameInFg: #e6e9ef;
historyFileNameOutFg: #e6e9ef;
historyOutIconFg: #9ea4b0;
historyOutIconFgSelected: #ffffff;
historyIconFgInverted: #e6e9ef;

 filterInputInactiveBg: #111215;
filterInputActiveBg: #181a20;
filterInputBorderFg: #2e323b;

menuBg: #16181c;
menuBgOver: #23272f;
menuFgDisabled: #5c626d;
menuIconFg: #828894;
menuIconFgOver: #e6e9ef;
menuSubmenuArrowFg: #828894;

scrollBarBg: #3a3f4888;
scrollBarBgOver: #5c626dcc;
scrollBg: #12131600;
scrollBgOver: #181a2044;

activeButtonBg: #2b2f38;
activeButtonBgOver: #363b46;
activeButtonBgRipple: #454a56;
activeButtonFg: #ffffff;
activeButtonFgOver: #ffffff;
activeButtonSecondaryFg: #b0b6c0;
lightButtonBg: #1b1e24;
lightButtonBgOver: #252932;
lightButtonBgRipple: #303540;
lightButtonFg: #d4d8de;
lightButtonFgOver: #ffffff;

boxBg: #16181c;
boxTextFg: #d4d8de;
boxTextFgGood: #8fa398;
boxTextFgError: #b08282;
boxTitleFg: #e6e9ef;
boxSearchBg: #121316;
"""

theme_zip = os.path.join(CFG_DIR, "Studio-Grey.tdesktop-theme")
bg_img = os.path.join(HOME, ".cache/cyberdeck/work_hud_bg.png")

with zipfile.ZipFile(theme_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("colors.tdesktop-theme", TG_COLORS)
    if os.path.isfile(bg_img):
        zf.write(bg_img, "background.png")
