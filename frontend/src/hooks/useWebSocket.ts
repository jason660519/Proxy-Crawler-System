/**
 * WebSocket Hook
 * 
 * 提供 WebSocket 連接管理功能，包括：
 * - 自動連接和重連
 * - 消息發送和接收
 * - 連接狀態管理
 * - 錯誤處理
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// ============= 類型定義 =============

/**
 * WebSocket 連接狀態
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * WebSocket 消息類型
 */
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp?: number;
}

/**
 * WebSocket 配置選項
 */
export interface WebSocketOptions {
  /** 自動重連 */
  autoReconnect?: boolean;
  /** 重連間隔（毫秒） */
  reconnectInterval?: number;
  /** 最大重連次數 */
  maxReconnectAttempts?: number;
  /** 心跳間隔（毫秒） */
  heartbeatInterval?: number;
  /** 連接超時（毫秒） */
  connectionTimeout?: number;
  /** 調試模式 */
  debug?: boolean;
}

/**
 * WebSocket Hook 返回值
 */
export interface UseWebSocketReturn {
  /** 連接狀態 */
  state: WebSocketState;
  /** 是否已連接 */
  isConnected: boolean;
  /** 最後收到的消息 */
  lastMessage: WebSocketMessage | null;
  /** 發送消息 */
  sendMessage: (message: WebSocketMessage) => void;
  /** 手動連接 */
  connect: () => void;
  /** 手動斷開連接 */
  disconnect: () => void;
  /** 重連 */
  reconnect: () => void;
  /** 連接錯誤 */
  error: string | null;
  /** 重連次數 */
  reconnectCount: number;
}

// ============= 默認配置 =============

const DEFAULT_OPTIONS: Required<WebSocketOptions> = {
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
  connectionTimeout: 10000,
  debug: false
};

// ============= Hook 實現 =============

/**
 * WebSocket Hook
 * 
 * @param url WebSocket 服務器地址
 * @param options 配置選項
 * @returns WebSocket 管理對象
 */
export function useWebSocket(
  url: string | null,
  options: WebSocketOptions = {}
): UseWebSocketReturn {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  // ============= 狀態管理 =============
  
  const [state, setState] = useState<WebSocketState>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);
  
  // ============= Refs =============
  
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<WebSocketMessage[]>([]);
  
  // ============= 工具函數 =============
  
  const log = useCallback((message: string, ...args: any[]) => {
    if (opts.debug) {
      console.log(`[WebSocket] ${message}`, ...args);
    }
  }, [opts.debug]);
  
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
  }, []);
  
  // ============= 心跳機制 =============
  
  const startHeartbeat = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
    }
    
    heartbeatTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        log('Heartbeat sent');
        startHeartbeat(); // 繼續心跳
      }
    }, opts.heartbeatInterval);
  }, [opts.heartbeatInterval, log]);
  
  // ============= 連接管理 =============
  
  const connect = useCallback(() => {
    if (!url) {
      log('No URL provided, skipping connection');
      return;
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log('Already connected');
      return;
    }
    
    log('Connecting to:', url);
    setState('connecting');
    setError(null);
    clearTimeouts();
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      // 連接超時處理
      connectionTimeoutRef.current = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          log('Connection timeout');
          ws.close();
          setState('error');
          setError('連接超時');
        }
      }, opts.connectionTimeout);
      
      // 連接成功
      ws.onopen = () => {
        log('Connected successfully');
        setState('connected');
        setError(null);
        setReconnectCount(0);
        clearTimeouts();
        startHeartbeat();
        
        // 發送排隊的消息
        while (messageQueueRef.current.length > 0) {
          const message = messageQueueRef.current.shift();
          if (message) {
            ws.send(JSON.stringify(message));
          }
        }
      };
      
      // 接收消息
      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          log('Message received:', message);
          
          // 處理 pong 消息
          if (message.type === 'pong') {
            log('Pong received');
            return;
          }
          
          setLastMessage({
            ...message,
            timestamp: message.timestamp || Date.now()
          });
        } catch (err) {
          log('Failed to parse message:', event.data, err);
        }
      };
      
      // 連接關閉
      ws.onclose = (event) => {
        log('Connection closed:', event.code, event.reason);
        setState('disconnected');
        clearTimeouts();
        
        // 自動重連
        if (opts.autoReconnect && reconnectCount < opts.maxReconnectAttempts) {
          const newCount = reconnectCount + 1;
          setReconnectCount(newCount);
          log(`Attempting reconnect ${newCount}/${opts.maxReconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, opts.reconnectInterval);
        } else if (reconnectCount >= opts.maxReconnectAttempts) {
          log('Max reconnect attempts reached');
          setState('error');
          setError('達到最大重連次數');
        }
      };
      
      // 連接錯誤
      ws.onerror = (event) => {
        log('Connection error:', event);
        setState('error');
        setError('連接錯誤');
        clearTimeouts();
      };
      
    } catch (err) {
      log('Failed to create WebSocket:', err);
      setState('error');
      setError('創建 WebSocket 失敗');
    }
  }, [url, opts, reconnectCount, log, clearTimeouts, startHeartbeat]);
  
  const disconnect = useCallback(() => {
    log('Disconnecting...');
    clearTimeouts();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    setState('disconnected');
    setError(null);
    setReconnectCount(0);
  }, [log, clearTimeouts]);
  
  const reconnect = useCallback(() => {
    log('Manual reconnect triggered');
    setReconnectCount(0);
    disconnect();
    setTimeout(connect, 100);
  }, [log, disconnect, connect]);
  
  // ============= 消息發送 =============
  
  const sendMessage = useCallback((message: WebSocketMessage) => {
    const messageWithTimestamp = {
      ...message,
      timestamp: message.timestamp || Date.now()
    };
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(messageWithTimestamp));
        log('Message sent:', messageWithTimestamp);
      } catch (err) {
        log('Failed to send message:', err);
        setError('發送消息失敗');
      }
    } else {
      log('WebSocket not connected, queuing message:', messageWithTimestamp);
      messageQueueRef.current.push(messageWithTimestamp);
    }
  }, [log]);
  
  // ============= 生命週期 =============
  
  useEffect(() => {
    if (url) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [url]); // 只在 URL 變化時重新連接
  
  // ============= 返回值 =============
  
  return {
    state,
    isConnected: state === 'connected',
    lastMessage,
    sendMessage,
    connect,
    disconnect,
    reconnect,
    error,
    reconnectCount
  };
}

// ============= 導出 =============

export default useWebSocket;