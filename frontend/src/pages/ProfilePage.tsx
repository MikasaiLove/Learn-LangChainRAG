import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Layout, Form, Input, Button, Card, message, Typography, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import * as authApi from '../api/auth';
import { useAuthStore } from '../stores/authStore';

const { Content } = Layout;
const { Title } = Typography;

const ProfilePage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const onFinish = async (values: { oldPassword: string; newPassword: string; confirm: string }) => {
    if (values.newPassword !== values.confirm) {
      message.error('两次新密码输入不一致');
      return;
    }
    setLoading(true);
    try {
      await authApi.changePassword(values.oldPassword, values.newPassword);
      message.success('密码修改成功，请重新登录');
      localStorage.clear();
      navigate('/login');
    } catch (err: any) {
      message.error(err.response?.data?.detail || '修改失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Card style={{ width: 450, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
          <Space style={{ marginBottom: 24 }}>
            <Link to="/chat"><Button icon={<ArrowLeftOutlined />}>返回</Button></Link>
            <Title level={4} style={{ margin: 0 }}>修改密码</Title>
          </Space>
          <div style={{ marginBottom: 16 }}>
            <Typography.Text>当前用户：<strong>{user?.username}</strong></Typography.Text>
          </div>
          <Form onFinish={onFinish} layout="vertical" size="large">
            <Form.Item
              name="oldPassword"
              label="旧密码"
              rules={[{ required: true, message: '请输入旧密码' }]}
            >
              <Input.Password />
            </Form.Item>
            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password />
            </Form.Item>
            <Form.Item
              name="confirm"
              label="确认新密码"
              rules={[{ required: true, message: '请确认新密码' }]}
            >
              <Input.Password />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Content>
    </Layout>
  );
};

export default ProfilePage;
