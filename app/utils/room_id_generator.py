"""
Room ID Generator
CNVS_IDT_ID 생성 및 파싱

형식: {user_id}_{timestamp}{microseconds}
예: user123_20251022104412345678
"""
from datetime import datetime
from typing import Dict


def generate_room_id(user_id: str) -> str:
    """
    Room ID 생성

    Args:
        user_id: 사용자 ID

    Returns:
        str: {user_id}_{timestamp}{microseconds}
            - timestamp: 14자리 (YYYYMMDDHH24MISS)
            - microseconds: 6자리 (000000-999999)

    Example:
        >>> generate_room_id("user123")
        'user123_20251022104412345678'
    """
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')  # 14자리
    microseconds = f"{now.microsecond % 1000000:06d}"  # 6자리
    return f"{user_id}_{timestamp}{microseconds}"


def parse_room_id(room_id: str) -> Dict[str, str]:
    """
    Room ID 파싱

    Args:
        room_id: 대화방 ID

    Returns:
        dict: {
            "user_id": str,
            "timestamp": str (14자리),
            "microseconds": str (6자리)
        }

    Raises:
        ValueError: 형식이 올바르지 않은 경우

    Example:
        >>> parse_room_id("user123_20251022104412345678")
        {
            "user_id": "user123",
            "timestamp": "20251022104412",
            "microseconds": "345678"
        }
    """
    parts = room_id.split("_")
    if len(parts) != 2:
        raise ValueError(f"Invalid room_id format: {room_id}")

    user_id = parts[0]
    time_part = parts[1]

    if len(time_part) != 20:  # 14 + 6
        raise ValueError(f"Invalid time part length: {time_part}")

    timestamp = time_part[:14]
    microseconds = time_part[14:]

    return {
        "user_id": user_id,
        "timestamp": timestamp,
        "microseconds": microseconds
    }


def validate_room_id_format(room_id: str) -> bool:
    """
    Room ID 형식 검증

    Args:
        room_id: 검증할 대화방 ID

    Returns:
        bool: 형식이 올바른지 여부
    """
    try:
        parsed = parse_room_id(room_id)
        # user_id는 비어있지 않아야 함
        if not parsed["user_id"]:
            return False
        # timestamp는 숫자여야 함
        int(parsed["timestamp"])
        int(parsed["microseconds"])
        return True
    except (ValueError, IndexError):
        return False
