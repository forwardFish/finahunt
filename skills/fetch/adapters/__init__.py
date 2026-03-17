from skills.fetch.adapters.cls_telegraph import ClsTelegraphAdapter
from skills.fetch.adapters.jiuyangongshe import JiuyangongsheAdapter
from skills.fetch.adapters.xueqiu import XueqiuHotSpotAdapter

ADAPTERS = {
    "cls_telegraph_html": ClsTelegraphAdapter,
    "jiuyangongshe_live_html": JiuyangongsheAdapter,
    "xueqiu_hot_spot_html": XueqiuHotSpotAdapter,
}

__all__ = ["ADAPTERS", "ClsTelegraphAdapter", "JiuyangongsheAdapter", "XueqiuHotSpotAdapter"]
