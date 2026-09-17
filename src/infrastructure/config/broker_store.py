import json
from pathlib import Path

# 天勤免费版/专业版支持的期货公司（受限于 TqSdk，参见 tqsdk-brokers）
DEFAULT_GROUPS = {
    "天勤免费版": ["宏源期货", "徽商期货", "银河期货"],
    "天勤专业版": ["东方汇金", "光大期货", "国泰君安"],
}


class BrokerStore:
    """期货公司分组列表与当前选中项持久化到 broker.json。

    文件同时承载「支持哪些公司」与「用户选中哪家」，供交易账号页展示与恢复。
    """

    def __init__(self, path: str = "data/broker.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        """返回 {"groups": {组名: [公司...]}, "selected": 选中公司}；文件缺失时写入默认值。"""
        if not self.path.exists():
            return self._write_default()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            groups = data["groups"]
            if not isinstance(groups, dict):
                raise ValueError("groups must be an object")
            selected = data.get("selected")
            if not isinstance(selected, str):
                selected = ""
        except (OSError, ValueError, KeyError, TypeError):
            # 文件损坏时不覆盖用户文件，回退默认列表，由页面默认选中第一项
            groups = {name: list(names) for name, names in DEFAULT_GROUPS.items()}
            selected = ""
        return {"groups": groups, "selected": selected}

    def save_selected(self, name: str) -> None:
        data = self.load()
        data["selected"] = name
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _write_default(self) -> dict:
        groups = {name: list(names) for name, names in DEFAULT_GROUPS.items()}
        data = {"groups": groups, "selected": DEFAULT_GROUPS["天勤免费版"][0]}
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return data
