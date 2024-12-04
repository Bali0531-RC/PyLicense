from datetime import datetime

class License:
    def __init__(self, key, max_hwid, product):
        self.key = key
        self.max_hwid = max_hwid
        self.product = product
        self.hwids = []
        self.ips = []
        self.request_count = 0
        self.created_at = datetime.now()
        self.is_active = True

    def to_dict(self):
        return {
            "key": self.key,
            "max_hwid": self.max_hwid,
            "product": self.product,
            "hwids": self.hwids,
            "ips": self.ips,
            "request_count": self.request_count,
            "created_at": self.created_at,
            "is_active": self.is_active
        } 