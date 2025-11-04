/**
 * RoomId Store Tests
 *
 * Test Coverage:
 * - Room ID 설정/초기화
 * - localStorage persistence
 * - XSS 방지
 * - 데이터 검증
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useRoomId } from '../roomIdStore_enhanced';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString(); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; }
  };
})();

global.localStorage = localStorageMock;

describe('RoomIdStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useRoomId.setState({ roomId: '' });
  });

  describe('Basic Functionality', () => {
    it('should initialize with empty room ID', () => {
      const { roomId } = useRoomId.getState();
      expect(roomId).toBe('');
    });

    it('should set room ID', () => {
      const testRoomId = 'user123_20251022104412345678';
      useRoomId.getState().setCurrentRoomId(testRoomId);

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe(testRoomId);
    });

    it('should clear room ID', () => {
      useRoomId.getState().setCurrentRoomId('test_room');
      useRoomId.getState().clearRoomId();

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe('');
    });
  });

  describe('Persistence', () => {
    it('should persist room ID to localStorage', () => {
      const testRoomId = 'user123_20251022104412345678';
      useRoomId.getState().setCurrentRoomId(testRoomId);

      const stored = localStorage.getItem('exGpt-room-id');
      expect(stored).toBe(testRoomId);
    });

    it('should load room ID from localStorage on init', () => {
      const testRoomId = 'user123_20251022104412345678';
      localStorage.setItem('exGpt-room-id', testRoomId);

      // Re-initialize store
      useRoomId.getState().initRoomId();

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe(testRoomId);
    });

    it('should clear localStorage on clearRoomId', () => {
      useRoomId.getState().setCurrentRoomId('test_room');
      useRoomId.getState().clearRoomId();

      const stored = localStorage.getItem('exGpt-room-id');
      expect(stored).toBeNull();
    });
  });

  describe('Validation', () => {
    it('should validate room ID format', () => {
      const validRoomId = 'user123_20251022104412345678';
      const result = useRoomId.getState().setCurrentRoomId(validRoomId);

      expect(result).toBe(true);
      expect(useRoomId.getState().roomId).toBe(validRoomId);
    });

    it('should reject invalid room ID format', () => {
      const invalidRoomId = '../../etc/passwd';
      const result = useRoomId.getState().setCurrentRoomId(invalidRoomId);

      expect(result).toBe(false);
      expect(useRoomId.getState().roomId).toBe('');
    });

    it('should reject XSS attempts in room ID', () => {
      const xssRoomId = '<script>alert("XSS")</script>';
      const result = useRoomId.getState().setCurrentRoomId(xssRoomId);

      expect(result).toBe(false);
      expect(useRoomId.getState().roomId).toBe('');
    });

    it('should reject empty room ID', () => {
      const result = useRoomId.getState().setCurrentRoomId('');

      expect(result).toBe(false);
      expect(useRoomId.getState().roomId).toBe('');
    });

    it('should reject excessively long room ID', () => {
      const longRoomId = 'a'.repeat(300);
      const result = useRoomId.getState().setCurrentRoomId(longRoomId);

      expect(result).toBe(false);
      expect(useRoomId.getState().roomId).toBe('');
    });
  });

  describe('Security', () => {
    it('should sanitize localStorage data on load', () => {
      // Inject malicious data
      localStorage.setItem('exGpt-room-id', '<script>alert("XSS")</script>');

      useRoomId.getState().initRoomId();

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe(''); // Should be rejected
    });

    it('should handle corrupted localStorage data', () => {
      localStorage.setItem('exGpt-room-id', 'null');

      useRoomId.getState().initRoomId();

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe('');
    });

    it('should not store sensitive information', () => {
      const roomId = 'user123_20251022104412345678';
      useRoomId.getState().setCurrentRoomId(roomId);

      const stored = localStorage.getItem('exGpt-room-id');
      expect(stored).not.toContain('password');
      expect(stored).not.toContain('token');
      expect(stored).not.toContain('secret');
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid consecutive updates', () => {
      const roomIds = [
        'user1_20251022104412345678',
        'user2_20251022104412345679',
        'user3_20251022104412345680',
      ];

      roomIds.forEach(id => useRoomId.getState().setCurrentRoomId(id));

      const { roomId } = useRoomId.getState();
      expect(roomId).toBe(roomIds[roomIds.length - 1]);
    });

    it('should handle localStorage quota exceeded', () => {
      // Mock quota exceeded error
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = vi.fn(() => {
        throw new Error('QuotaExceededError');
      });

      const result = useRoomId.getState().setCurrentRoomId('test_room');

      // Should handle gracefully
      expect(result).toBeDefined();

      localStorage.setItem = originalSetItem;
    });
  });
});
