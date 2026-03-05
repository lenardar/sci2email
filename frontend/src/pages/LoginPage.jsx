import { Button, Card, Form, Input, Typography, message } from "antd";
import client from "../services/api";

export default function LoginPage({ onLogin }) {
  const [form] = Form.useForm();

  const submit = async (values) => {
    try {
      const { data } = await client.post("/api/auth/login", values);
      localStorage.setItem("token", data.access_token);
      onLogin();
    } catch {
      message.error("登录失败，请检查用户名密码");
    }
  };

  return (
    <Card className="auth-card glass">
      <Typography.Title level={3} style={{ marginTop: 4 }}>
        Sci2Email 登录
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        管理 RSS 订阅与定时邮件推送
      </Typography.Paragraph>
      <Form form={form} layout="vertical" onFinish={submit} initialValues={{ username: "admin", password: "admin123" }}>
        <Form.Item label="用户名" name="username" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="密码" name="password" rules={[{ required: true }]}>
          <Input.Password />
        </Form.Item>
        <Button type="primary" htmlType="submit" block>
          登录后台
        </Button>
      </Form>
    </Card>
  );
}
