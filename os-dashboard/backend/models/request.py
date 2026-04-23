from dataclasses import dataclass


@dataclass
class DiskRequest:
    track: int
    order: int = 0

    def to_dict(self):
        return {"track": self.track, "order": self.order}

    @classmethod
    def from_dict(cls, data: dict, order: int = 0) -> "DiskRequest":
        return cls(track=int(data) if isinstance(data, (int, float)) else int(data["track"]), order=order)
