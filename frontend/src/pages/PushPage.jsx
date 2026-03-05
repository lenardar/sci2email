import { Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Switch, Table, Tag, message } from "antd";
import { useEffect, useState } from "react";
import client from "../services/api";

const parseTimes = (value) =>
  value
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);

export default function PushPage() {
  const [recipients, setRecipients] = useState([]);
  const [sources, setSources] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [smtpInfo, setSmtpInfo] = useState(null);
  const [aiInfo, setAiInfo] = useState(null);
  const [rForm] = Form.useForm();
  const [tForm] = Form.useForm();
  const [smtpForm] = Form.useForm();
  const [aiForm] = Form.useForm();

  const load = async () => {
    const [r, s, t, smtp, ai] = await Promise.all([
      client.get("/api/push/recipients"),
      client.get("/api/rss/sources"),
      client.get("/api/push/tasks"),
      client.get("/api/push/smtp-settings"),
      client.get("/api/push/ai-settings"),
    ]);
    setRecipients(r.data);
    setSources(s.data);
    setTasks(t.data);
    setSmtpInfo(smtp.data);
    setAiInfo(ai.data);
    smtpForm.setFieldsValue({
      smtp_host: smtp.data.smtp_host,
      smtp_port: smtp.data.smtp_port,
      smtp_username: smtp.data.smtp_username,
      smtp_from_email: smtp.data.smtp_from_email,
      smtp_use_tls: smtp.data.smtp_use_tls,
      smtp_password: "",
    });
    aiForm.setFieldsValue({
      ai_enabled: ai.data.ai_enabled,
      ai_base_url: ai.data.ai_base_url,
      ai_model: ai.data.ai_model,
      ai_timeout_seconds: ai.data.ai_timeout_seconds,
      ai_api_key: "",
    });
  };

  useEffect(() => {
    load();
  }, []);

  const addRecipient = async (values) => {
    await client.post("/api/push/recipients", values);
    rForm.resetFields();
    load();
  };

  const addTask = async (values) => {
    await client.post("/api/push/tasks", { ...values, send_times: parseTimes(values.send_times) });
    tForm.resetFields();
    load();
  };

  const saveSmtp = async (values) => {
    await client.put("/api/push/smtp-settings", values);
    message.success("系统推送邮箱配置已保存");
    load();
  };

  const saveAi = async (values) => {
    await client.put("/api/push/ai-settings", values);
    message.success("AI 配置已保存");
    load();
  };

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card className="glass" title="AI 配置">
          <Form form={aiForm} layout="vertical" onFinish={saveAi}>
            <Row gutter={12}>
              <Col xs={24} md={5}>
                <Form.Item label="启用 AI" name="ai_enabled" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
              <Col xs={24} md={9}>
                <Form.Item label="API Base URL" name="ai_base_url" rules={[{ required: true }]}>
                  <Input placeholder="https://api.openai.com/v1" />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item label="模型" name="ai_model" rules={[{ required: true }]}>
                  <Input placeholder="gpt-4o-mini" />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="超时(秒)" name="ai_timeout_seconds" rules={[{ required: true }]}>
                  <InputNumber min={5} max={300} style={{ width: "100%" }} />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={12}>
              <Col xs={24} md={10}>
                <Form.Item label="AI API Key" name="ai_api_key">
                  <Input.Password placeholder={aiInfo?.has_ai_api_key ? "已保存，留空表示不修改" : "请输入 API Key"} />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit">
              保存 AI 配置
            </Button>
          </Form>
        </Card>
      </Col>

      <Col span={24}>
        <Card className="glass" title="系统推送邮箱配置">
          <Form form={smtpForm} layout="vertical" onFinish={saveSmtp}>
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item label="SMTP 主机" name="smtp_host" rules={[{ required: true }]}>
                  <Input placeholder="smtp.qq.com / smtp.gmail.com" />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="端口" name="smtp_port" rules={[{ required: true }]}>
                  <InputNumber min={1} max={65535} style={{ width: "100%" }} />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item label="系统发件邮箱" name="smtp_username" rules={[{ required: true, type: "email" }]}>
                  <Input placeholder="your_email@example.com" />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item label="显示发件邮箱" name="smtp_from_email" rules={[{ required: true, type: "email" }]}>
                  <Input placeholder="your_email@example.com" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item label="邮箱授权码" name="smtp_password">
                  <Input.Password placeholder={smtpInfo?.has_smtp_password ? "已保存，留空表示不修改" : "请输入授权码"} />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="SSL/TLS" name="smtp_use_tls" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit">
              保存邮箱配置
            </Button>
          </Form>
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card className="glass" title="收件人">
          <Form form={rForm} layout="vertical" onFinish={addRecipient}>
            <Form.Item label="邮箱" name="email" rules={[{ required: true, type: "email" }]}>
              <Input placeholder="name@example.com" />
            </Form.Item>
            <Form.Item label="启用" name="enabled" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
            <Button type="primary" htmlType="submit" block>
              添加收件人
            </Button>
          </Form>
        </Card>
      </Col>
      <Col xs={24} lg={16}>
        <Card className="glass" title="创建推送任务">
          <Form
            form={tForm}
            layout="vertical"
            onFinish={addTask}
            initialValues={{
              enabled: true,
              timezone: "Asia/Shanghai",
              send_times: "09:00,18:00",
              max_items: 20,
            }}
          >
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item label="任务名" name="name" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={24} md={8}>
                <Form.Item label="时区" name="timezone" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={24} md={8}>
                <Form.Item label="时间点(HH:mm,逗号分隔)" name="send_times" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item label="订阅源" name="source_ids" rules={[{ required: true }]}>
                  <Select mode="multiple" options={sources.map((s) => ({ label: s.name, value: s.id }))} />
                </Form.Item>
              </Col>
              <Col xs={24} md={8}>
                <Form.Item label="收件人" name="recipient_ids" rules={[{ required: true }]}>
                  <Select mode="multiple" options={recipients.map((r) => ({ label: r.email, value: r.id }))} />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="每封条数" name="max_items">
                  <InputNumber min={1} max={100} style={{ width: "100%" }} />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="启用" name="enabled" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit">
              保存任务
            </Button>
          </Form>
        </Card>
      </Col>

      <Col span={24}>
        <Card className="glass" title="任务列表">
          <Table
            rowKey="id"
            dataSource={tasks}
            pagination={{ pageSize: 6 }}
            columns={[
              { title: "任务", dataIndex: "name" },
              { title: "时间点", dataIndex: "send_times", render: (v) => v.map((x) => <Tag key={x}>{x}</Tag>) },
              { title: "时区", dataIndex: "timezone" },
              { title: "源数量", dataIndex: "source_ids", render: (v) => v.length },
              { title: "收件人数", dataIndex: "recipient_ids", render: (v) => v.length },
              { title: "状态", dataIndex: "enabled", render: (v) => <Tag color={v ? "blue" : "default"}>{v ? "启用" : "停用"}</Tag> },
              {
                title: "操作",
                render: (_, row) => (
                  <Space>
                    <Button size="small" onClick={async () => { await client.post(`/api/push/tasks/${row.id}/run`); message.success("已触发手动推送"); }}>
                      立即执行
                    </Button>
                    <Button size="small" danger onClick={async () => { await client.delete(`/api/push/tasks/${row.id}`); load(); }}>
                      删除
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );
}
