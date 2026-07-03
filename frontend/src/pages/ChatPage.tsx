import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout, Input, Button, List, Typography, message, Spin, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, MessageOutlined, SendOutlined, LogoutOutlined, SettingOutlined, PictureOutlined, ClearOutlined } from '@ant-design/icons';
import { useAuthStore } from '../stores/authStore';
import * as chatApi from '../api/chat';
import type { Session, Message, Citation } from '../api/chat';
import ReactMarkdown from 'react-markdown';

const { Sider, Content, Header } = Layout;
const { Text } = Typography;

const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const [sessions, setSessions] = useState<Session[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [streaming, setStreaming] = useState('');
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 背景图片
  const [bgImage, setBgImage] = useState<string>(() => {
    return localStorage.getItem('chat_bg_image') || '';
  });

  // Load sessions
  const loadSessions = useCallback(async () => {
    try {
      const res = await chatApi.getSessions(1, 50);
      setSessions(res.items);
    } catch { /* ignore */ }
  }, []);

  // Load messages for current session
  const loadMessages = useCallback(async (sid: string) => {
    setLoading(true);
    try {
      const res = await chatApi.getMessages(sid, 1, 200);
      setMessages(res.items);
    } catch {
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId);
      setStreaming('');
      setStreamingCitations([]);
    }
  }, [sessionId, loadMessages]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  const handleNewSession = async () => {
    try {
      const session = await chatApi.createSession();
      setSessions((prev) => [session, ...prev]);
      navigate(`/chat/${session.id}`);
    } catch {
      message.error('创建会话失败');
    }
  };

  const handleDeleteSession = async (sid: string) => {
    try {
      await chatApi.deleteSession(sid);
      setSessions((prev) => prev.filter((s) => s.id !== sid));
      if (sessionId === sid) {
        navigate('/chat');
      }
    } catch {
      message.error('删除失败');
    }
  };

  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || sending) return;
    if (!sessionId) {
      // Auto-create session
      try {
        const session = await chatApi.createSession(content.slice(0, 30));
        setSessions((prev) => [session, ...prev]);
        navigate(`/chat/${session.id}`);
        setInputValue('');
        // Send after navigation
        setTimeout(() => sendMessage(session.id, content), 100);
        return;
      } catch {
        message.error('创建会话失败');
        return;
      }
    }

    sendMessage(sessionId, content);
  };

  const sendMessage = async (sid: string, content: string) => {
    setSending(true);
    setInputValue('');
    setStreaming('');

    // Add user message immediately
    const userMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: sid,
      role: 'user',
      content,
      citations: [],
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      let fullContent = '';
      let citations: Citation[] = [];

      for await (const event of chatApi.streamChat(sid, content)) {
        if (event.type === 'token') {
          fullContent += event.content;
          setStreaming(fullContent);
        } else if (event.type === 'citations') {
          citations = event.data;
          setStreamingCitations(citations);
        } else if (event.type === 'done') {
          const assistantMsg: Message = {
            id: event.message_id || `msg-${Date.now()}`,
            session_id: sid,
            role: 'assistant',
            content: fullContent,
            citations: event.citations || citations,
            tokens: event.tokens,
          };
          setMessages((prev) => [...prev, assistantMsg]);
          setStreaming('');
          setStreamingCitations([]);
          loadSessions(); // Refresh session titles
        } else if (event.type === 'error') {
          message.error(event.message);
        }
      }
    } catch (err: any) {
      message.error('发送失败: ' + (err.message || '未知错误'));
    } finally {
      setSending(false);
    }
  };

  const handleRegenerate = async () => {
    if (!sessionId || sending) return;
    setSending(true);
    setStreaming('');

    // Remove last assistant message
    setMessages((prev) => {
      const lastAssistant = [...prev].reverse().findIndex((m) => m.role === 'assistant');
      if (lastAssistant >= 0) {
        return prev.slice(0, prev.length - lastAssistant - 1);
      }
      return prev;
    });

    try {
      let fullContent = '';
      let citations: Citation[] = [];

      for await (const event of chatApi.regenerateStream(sessionId)) {
        if (event.type === 'token') {
          fullContent += event.content;
          setStreaming(fullContent);
        } else if (event.type === 'citations') {
          citations = event.data;
          setStreamingCitations(citations);
        } else if (event.type === 'done') {
          const assistantMsg: Message = {
            id: event.message_id || `msg-${Date.now()}`,
            session_id: sessionId,
            role: 'assistant',
            content: fullContent,
            citations: event.citations || citations,
            tokens: event.tokens,
          };
          setMessages((prev) => [...prev, assistantMsg]);
          setStreaming('');
          setStreamingCitations([]);
        } else if (event.type === 'error') {
          message.error(event.message);
        }
      }
    } catch {
      message.error('重新生成失败');
    } finally {
      setSending(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleBgImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      message.error('请选择图片文件');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const url = reader.result as string;
      setBgImage(url);
      localStorage.setItem('chat_bg_image', url);
    };
    reader.readAsDataURL(file);
  };

  const handleClearBg = () => {
    setBgImage('');
    localStorage.removeItem('chat_bg_image');
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={280} style={{ background: '#fff', borderRight: '1px solid #f0f0f0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          <Button type="primary" icon={<PlusOutlined />} block onClick={handleNewSession}>
            新建对话
          </Button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <List
            dataSource={sessions}
            renderItem={(s) => (
              <List.Item
                onClick={() => navigate(`/chat/${s.id}`)}
                style={{
                  cursor: 'pointer',
                  padding: '12px 16px',
                  background: sessionId === s.id ? '#e6f4ff' : 'transparent',
                }}
                actions={[
                  <Popconfirm key="del" title="确定删除此会话？" onConfirm={(e) => { e?.stopPropagation(); handleDeleteSession(s.id); }}>
                    <DeleteOutlined onClick={(e) => e?.stopPropagation()} />
                  </Popconfirm>,
                ]}
              >
                <MessageOutlined style={{ marginRight: 8 }} />
                <Text ellipsis style={{ flex: 1 }}>{s.title}</Text>
              </List.Item>
            )}
          />
        </div>
        <div style={{ padding: '12px 16px', borderTop: '1px solid #f0f0f0' }}>
          <Space>
            <Text strong>{user?.username}</Text>
            {user?.role === 'admin' && <Text type="secondary">(管理员)</Text>}
          </Space>
          <div style={{ marginTop: 8 }}>
            {user?.role === 'admin' && (
              <Button type="link" icon={<SettingOutlined />} onClick={() => navigate('/admin/kb')}>
                知识库管理
              </Button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleBgImageSelect}
            />
            <Button type="link" icon={<PictureOutlined />} onClick={() => fileInputRef.current?.click()}>
              聊天背景
            </Button>
            {bgImage && (
              <Button type="link" icon={<ClearOutlined />} onClick={handleClearBg} danger>
                清除背景
              </Button>
            )}
            <Button type="link" icon={<LogoutOutlined />} onClick={handleLogout} danger>
              退出
            </Button>
          </div>
        </div>
      </Sider>

      <Layout>
        <Content style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
          <div style={{
            flex: 1,
            overflow: 'auto',
            padding: '24px 48px',
            backgroundImage: bgImage ? `url(${bgImage})` : undefined,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
            backgroundAttachment: 'fixed',
            position: 'relative',
          }}>
            {loading ? (
              <div style={{ textAlign: 'center', marginTop: 100 }}><Spin size="large" /></div>
            ) : messages.length === 0 && !streaming ? (
              <div style={{ textAlign: 'center', marginTop: 100, color: '#999' }}>
                <MessageOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>选择一个会话或新建对话开始问答</div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <div key={msg.id} style={{
                    marginBottom: 24,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}>
                    <div style={{ marginBottom: 6 }}>
                      <Text strong style={{ color: msg.role === 'user' ? '#1677ff' : '#52c41a' }}>
                        {msg.role === 'user' ? user?.username || '我' : 'AI 助手'}
                      </Text>
                    </div>
                    <div style={{
                      background: msg.role === 'user' ? '#1677ff' : '#ffffff',
                      border: msg.role === 'user' ? 'none' : '1px solid #e0e0e0',
                      color: msg.role === 'user' ? '#fff' : '#333',
                      padding: '10px 16px',
                      borderRadius: msg.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
                      maxWidth: '75%',
                      wordBreak: 'break-word',
                    }}>
                      {msg.role === 'assistant' ? (
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      ) : (
                        <Text style={{ color: '#fff' }}>{msg.content}</Text>
                      )}
                      {msg.role === 'assistant' && msg.tokens && (
                        <div style={{ textAlign: 'right', marginTop: 6 }}>
                          <Text type="secondary" style={{ fontSize: 11 }}>
                            Tokens: {msg.tokens.total} (in:{msg.tokens.input} out:{msg.tokens.output})
                          </Text>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {streaming && (
                  <div style={{ marginBottom: 24, display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <div style={{ marginBottom: 6 }}>
                      <Text strong style={{ color: '#52c41a' }}>AI 助手</Text>
                    </div>
                    <div style={{
                      background: '#ffffff',
                      border: '1px solid #e0e0e0',
                      color: '#333',
                      padding: '10px 16px',
                      borderRadius: '12px 12px 12px 4px',
                      maxWidth: '75%',
                      wordBreak: 'break-word',
                    }}>
                      <ReactMarkdown>{streaming}</ReactMarkdown>
                      <Text type="secondary" style={{ animation: 'blink 1s infinite' }}>▌</Text>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <div style={{ padding: '16px 48px', borderTop: '1px solid #f0f0f0', background: '#fff' }}>
            <div style={{ display: 'flex', gap: 12, maxWidth: 900, margin: '0 auto' }}>
              <Input.TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="输入您关于商品的问题... (Enter 发送, Shift+Enter 换行)"
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={sending}
              />
              <Space>
                <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={sending}>
                  发送
                </Button>
                {messages.length > 0 && (
                  <Button onClick={handleRegenerate} disabled={sending}>
                    重新生成
                  </Button>
                )}
              </Space>
            </div>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default ChatPage;
