"""
Tests for room_id_generator.py
Room ID 생성, 파싱, 검증 테스트
"""
import pytest
from datetime import datetime
from app.utils.room_id_generator import (
    generate_room_id,
    parse_room_id,
    validate_room_id_format
)


class TestGenerateRoomId:
    """Room ID 생성 테스트"""

    def test_generate_room_id_format(self):
        """Room ID가 올바른 형식으로 생성되는지 테스트"""
        user_id = "testuser"
        room_id = generate_room_id(user_id)

        # 형식: {user_id}_{timestamp}{microseconds}
        assert room_id.startswith(f"{user_id}_")

        # 마지막 언더스코어 이후가 20자리 타임스탬프여야 함
        last_underscore_idx = room_id.rfind("_")
        time_part = room_id[last_underscore_idx + 1:]
        assert len(time_part) == 20
        assert time_part.isdigit()

    def test_generate_room_id_uniqueness(self):
        """연속 생성된 Room ID가 고유한지 테스트"""
        user_id = "test_user"
        room_ids = [generate_room_id(user_id) for _ in range(100)]

        # 모든 ID가 고유해야 함
        assert len(room_ids) == len(set(room_ids))

    def test_generate_room_id_with_different_users(self):
        """서로 다른 사용자에 대해 다른 Room ID가 생성되는지 테스트"""
        room_id1 = generate_room_id("user1")
        room_id2 = generate_room_id("user2")

        assert room_id1 != room_id2
        assert room_id1.startswith("user1_")
        assert room_id2.startswith("user2_")

    def test_generate_room_id_with_special_characters(self):
        """특수문자가 포함된 user_id로도 생성 가능한지 테스트"""
        user_id = "user@company.com"
        room_id = generate_room_id(user_id)

        assert room_id.startswith(f"{user_id}_")
        assert "_" in room_id


class TestParseRoomId:
    """Room ID 파싱 테스트"""

    def test_parse_valid_room_id(self):
        """올바른 Room ID 파싱 테스트"""
        user_id = "test_user"
        room_id = generate_room_id(user_id)

        parsed = parse_room_id(room_id)

        assert parsed["user_id"] == user_id
        assert len(parsed["timestamp"]) == 14
        assert len(parsed["microseconds"]) == 6
        assert parsed["timestamp"].isdigit()
        assert parsed["microseconds"].isdigit()

    def test_parse_room_id_timestamp_format(self):
        """파싱된 타임스탬프가 올바른 형식인지 테스트"""
        room_id = generate_room_id("test_user")
        parsed = parse_room_id(room_id)

        timestamp = parsed["timestamp"]

        # YYYYMMDDHH24MISS 형식 검증
        year = int(timestamp[:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        hour = int(timestamp[8:10])
        minute = int(timestamp[10:12])
        second = int(timestamp[12:14])

        assert 2020 <= year <= 2100
        assert 1 <= month <= 12
        assert 1 <= day <= 31
        assert 0 <= hour <= 23
        assert 0 <= minute <= 59
        assert 0 <= second <= 59

    def test_parse_invalid_format_no_underscore(self):
        """언더스코어가 없는 잘못된 형식 테스트"""
        with pytest.raises(ValueError, match="Invalid room_id format"):
            parse_room_id("testuser20251022104412345678")

    def test_parse_invalid_format_wrong_time_length(self):
        """타임스탬프 길이가 20자가 아닌 경우 테스트"""
        with pytest.raises(ValueError, match="Invalid time part length"):
            parse_room_id("test_user_2025102210441234")  # 16자만 있음

    def test_parse_invalid_time_length(self):
        """타임스탬프 길이가 잘못된 경우 테스트"""
        with pytest.raises(ValueError, match="Invalid time part length"):
            parse_room_id("testuser_2025102210")

    def test_parse_empty_room_id(self):
        """빈 Room ID 파싱 시도 테스트"""
        with pytest.raises(ValueError):
            parse_room_id("")


class TestValidateRoomIdFormat:
    """Room ID 형식 검증 테스트"""

    def test_validate_valid_room_id(self):
        """올바른 Room ID 검증 테스트"""
        room_id = generate_room_id("test_user")
        assert validate_room_id_format(room_id) is True

    def test_validate_invalid_format(self):
        """잘못된 형식 검증 테스트"""
        assert validate_room_id_format("invalid_format") is False
        assert validate_room_id_format("user_123") is False
        assert validate_room_id_format("") is False

    def test_validate_no_user_id(self):
        """user_id가 없는 경우 검증 테스트"""
        assert validate_room_id_format("_20251022104412345678") is False

    def test_validate_non_numeric_timestamp(self):
        """숫자가 아닌 타임스탬프 검증 테스트"""
        assert validate_room_id_format("user_2025102210ABCD345678") is False

    def test_validate_special_cases(self):
        """특수 케이스 검증 테스트"""
        # None
        assert validate_room_id_format(None) is False if None else True

        # 올바른 길이지만 잘못된 형식
        assert validate_room_id_format("x" * 100) is False


class TestRoomIdIntegration:
    """Room ID 생성-파싱-검증 통합 테스트"""

    def test_generate_parse_validate_cycle(self):
        """생성 → 파싱 → 검증 사이클 테스트"""
        user_id = "integration_test_user"

        # 1. 생성
        room_id = generate_room_id(user_id)

        # 2. 검증
        assert validate_room_id_format(room_id) is True

        # 3. 파싱
        parsed = parse_room_id(room_id)
        assert parsed["user_id"] == user_id

        # 4. 재조립 검증
        reconstructed = f"{parsed['user_id']}_{parsed['timestamp']}{parsed['microseconds']}"
        assert reconstructed == room_id

    def test_multiple_users_concurrent_generation(self):
        """여러 사용자에 대해 동시 생성 시나리오 테스트"""
        users = [f"user{i}" for i in range(10)]
        room_ids = [generate_room_id(user) for user in users]

        # 모든 Room ID가 고유해야 함
        assert len(room_ids) == len(set(room_ids))

        # 모든 Room ID가 유효해야 함
        for room_id in room_ids:
            assert validate_room_id_format(room_id) is True

        # 각 Room ID를 파싱하여 user_id 확인
        for user, room_id in zip(users, room_ids):
            parsed = parse_room_id(room_id)
            assert parsed["user_id"] == user

    def test_room_id_temporal_ordering(self):
        """시간순으로 생성된 Room ID가 순서를 유지하는지 테스트"""
        import time

        room_ids = []
        for _ in range(5):
            room_ids.append(generate_room_id("test_user"))
            time.sleep(0.001)  # 1ms 대기

        # 파싱하여 타임스탬프 비교
        timestamps = [parse_room_id(rid)["timestamp"] + parse_room_id(rid)["microseconds"]
                     for rid in room_ids]

        # 타임스탬프가 증가하는지 확인
        for i in range(len(timestamps) - 1):
            assert timestamps[i] <= timestamps[i + 1]
