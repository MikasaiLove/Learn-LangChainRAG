import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Layout, Table, Upload, Button, message, Space, Tag, Input, Typography, Popconfirm, Statistic, Row, Col, Card } from 'antd';
import { UploadOutlined, DeleteOutlined, ArrowLeftOutlined, InboxOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import * as kbApi from '../api/knowledge';
import type { Document } from '../api/knowledge';

const { Content } = Layout;
const { Title } = Typography;
const { Dragger } = Upload;

const KBManagementPage: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [stats, setStats] = useState({ document_count: 0, indexed_count: 0, total_chunks: 0, total_chars: 0 });

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await kbApi.getDocuments({ page, size: 20, search: search || undefined });
      setDocuments(res.items);
      setTotal(res.total);
    } catch {
      message.error('加载文档列表失败');
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  const loadStats = useCallback(async () => {
    try {
      const res = await kbApi.getStats();
      setStats(res);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadDocuments();
    loadStats();
  }, [loadDocuments, loadStats]);

  const handleUpload = async (file: File) => {
    try {
      await kbApi.uploadDocument(file);
      message.success(`"${file.name}" 上传成功，正在处理中...`);
      loadDocuments();
      loadStats();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '上传失败');
    }
    return false; // Prevent default upload
  };

  const handleDelete = async (docId: string) => {
    try {
      await kbApi.deleteDocument(docId);
      message.success('文档已删除');
      loadDocuments();
      loadStats();
    } catch {
      message.error('删除失败');
    }
  };

  const statusTag = (status: string) => {
    const map: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '待处理' },
      processing: { color: 'processing', text: '处理中' },
      done: { color: 'success', text: '已完成' },
      fail: { color: 'error', text: '失败' },
    };
    const item = map[status] || { color: 'default', text: status };
    return <Tag color={item.color}>{item.text}</Tag>;
  };

  const fileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)}MB`;
  };

  const charSize = (chars: number) => {
    if (chars < 1000) return `${chars} 字`;
    if (chars < 1000000) return `${(chars / 1000).toFixed(1)}K 字`;
    return `${(chars / 1000000).toFixed(1)}M 字`;
  };

  const columns: ColumnsType<Document> = [
    { title: '文件名', dataIndex: 'filename', key: 'filename', ellipsis: true },
    { title: '类型', dataIndex: 'file_type', key: 'file_type', width: 80, render: (t: string) => <Tag>{t.toUpperCase()}</Tag> },
    { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 100, render: (s: number) => fileSize(s) },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (s: string) => statusTag(s) },
    { title: '字符数', dataIndex: 'char_count', key: 'char_count', width: 100 },
    { title: '分块数', dataIndex: 'chunk_count', key: 'chunk_count', width: 80 },
    {
      title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 180,
      render: (t: string) => t ? new Date(t).toLocaleString() : '-',
    },
    {
      title: '操作', key: 'actions', width: 80,
      render: (_, record) => (
        <Popconfirm title="确定删除此文档？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: 24, maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Space>
            <Link to="/chat"><Button icon={<ArrowLeftOutlined />}>返回问答</Button></Link>
            <Title level={3} style={{ margin: 0 }}>知识库管理</Title>
          </Space>
        </div>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card><Statistic title="文档总数" value={stats.document_count} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="已索引" value={stats.indexed_count} valueStyle={{ color: '#52c41a' }} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="总分块数" value={stats.total_chunks} /></Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="总字符量"
                value={charSize(stats.total_chars)}
                valueStyle={{ fontSize: 20 }}
              />
            </Card>
          </Col>
        </Row>

        <Card style={{ marginBottom: 24 }}>
          <Dragger
            multiple
            showUploadList={false}
            beforeUpload={(file) => { handleUpload(file); return false; }}
            accept=".pdf,.docx,.txt,.md,.csv,.html"
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p>点击或拖拽文件到此区域上传</p>
            <p style={{ color: '#999' }}>支持 PDF、DOCX、TXT、Markdown、CSV、HTML 格式</p>
          </Dragger>
        </Card>

        <Card>
          <Space style={{ marginBottom: 16 }}>
            <Input.Search
              placeholder="搜索文件名"
              onSearch={(v) => { setSearch(v); setPage(1); }}
              style={{ width: 300 }}
              allowClear
            />
          </Space>
          <Table
            columns={columns}
            dataSource={documents}
            rowKey="id"
            loading={loading}
            pagination={{
              current: page,
              total,
              pageSize: 20,
              onChange: (p) => setPage(p),
              showTotal: (t) => `共 ${t} 个文档`,
            }}
          />
        </Card>
      </Content>
    </Layout>
  );
};

export default KBManagementPage;
