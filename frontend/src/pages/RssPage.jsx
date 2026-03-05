import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Segmented,
  Space,
  Statistic,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { useEffect, useState } from "react";
import client from "../services/api";

export default function RssPage() {
  const [mode, setMode] = useState("reader");
  const [groups, setGroups] = useState([]);
  const [sources, setSources] = useState([]);
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState({ source_count: 0, group_count: 0, entry_count: 0 });
  const [groupForm] = Form.useForm();
  const [sourceForm] = Form.useForm();
  const [filterForm] = Form.useForm();

  const loadMeta = async () => {
    const [g, s, r] = await Promise.all([
      client.get("/api/rss/groups"),
      client.get("/api/rss/sources"),
      client.get("/api/rss/stats"),
    ]);
    setGroups(g.data);
    setSources(s.data);
    setStats(r.data);
  };

  const loadEntries = async () => {
    const filters = filterForm.getFieldsValue();
    const { data } = await client.get("/api/rss/entries", {
      params: {
        group_id: filters.group_id || undefined,
        source_id: filters.source_id || undefined,
        q: filters.q || undefined,
        limit: 200,
      },
    });
    setEntries(data);
  };

  const loadAll = async () => {
    await Promise.all([loadMeta(), loadEntries()]);
  };

  useEffect(() => {
    loadAll();
  }, []);

  const addGroup = async (values) => {
    await client.post("/api/rss/groups", values);
    groupForm.resetFields();
    message.success("分组已创建");
    loadMeta();
  };

  const addSource = async (values) => {
    await client.post("/api/rss/sources", values);
    sourceForm.resetFields();
    message.success("订阅源已添加");
    loadMeta();
  };

  const pullNow = async () => {
    const { data } = await client.post("/api/rss/pull-now");
    message.success(`抓取完成，新增 ${data.added} 条`);
    loadAll();
  };

  const importOpml = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await client.post("/api/rss/import-opml", formData);
      message.success(`导入完成：新增 ${data.created}，更新 ${data.updated}，跳过 ${data.skipped}`);
      await loadAll();
    } catch (error) {
      message.error(error?.response?.data?.detail || "导入失败");
    } finally {
      event.target.value = "";
    }
  };

  const exportOpml = async () => {
    try {
      const response = await client.get("/api/rss/export-opml", { responseType: "blob" });
      const blob = new Blob([response.data], { type: "text/xml;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "rss-export.opml";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      message.error("导出失败");
    }
  };

  const readerPanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}>
        <Card className="glass">
          <Statistic title="订阅源" value={stats.source_count} />
        </Card>
      </Col>
      <Col xs={24} md={8}>
        <Card className="glass">
          <Statistic title="分组数" value={stats.group_count} />
        </Card>
      </Col>
      <Col xs={24} md={8}>
        <Card className="glass">
          <Statistic title="文章总量" value={stats.entry_count} />
        </Card>
      </Col>

      <Col span={24}>
        <Card className="glass" title="RSS 阅读器">
          <Form form={filterForm} layout="vertical">
            <Row gutter={12}>
              <Col xs={24} md={6}>
                <Form.Item label="分组筛选" name="group_id">
                  <Select allowClear options={groups.map((g) => ({ label: g.name, value: g.id }))} />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item label="订阅源筛选" name="source_id">
                  <Select allowClear options={sources.map((s) => ({ label: s.name, value: s.id }))} />
                </Form.Item>
              </Col>
              <Col xs={24} md={8}>
                <Form.Item label="关键词" name="q">
                  <Input placeholder="按标题搜索" />
                </Form.Item>
              </Col>
              <Col xs={24} md={4}>
                <Form.Item label="操作">
                  <Space>
                    <Button type="primary" onClick={loadEntries}>筛选</Button>
                    <Button onClick={pullNow}>抓取全部</Button>
                  </Space>
                </Form.Item>
              </Col>
            </Row>
          </Form>

          <Table
            rowKey="id"
            dataSource={entries}
            pagination={{ pageSize: 12 }}
            onExpand={async (expanded, row) => {
              if (!expanded) return;
              if (row.ai_status === "success" && row.summary_en && row.summary_zh) return;
              await client.post(`/api/rss/entries/${row.id}/ai-refresh`);
              loadEntries();
            }}
            expandable={{
              expandedRowRender: (row) => (
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <Tag color={row.ai_status === "success" ? "green" : row.ai_status === "failed" ? "red" : "gold"}>
                      AI: {row.ai_status}
                    </Tag>
                    <Button
                      size="small"
                      style={{ marginLeft: 8 }}
                      onClick={async () => {
                        await client.post(`/api/rss/entries/${row.id}/ai-refresh`);
                        message.success("AI 处理已刷新");
                        loadEntries();
                      }}
                    >
                      重新AI处理
                    </Button>
                  </div>
                  <Typography.Paragraph style={{ marginBottom: 6 }}>
                    <strong>中文摘要：</strong>
                    {row.summary_zh || "暂无"}
                  </Typography.Paragraph>
                  <Typography.Paragraph style={{ marginBottom: 0 }}>
                    <strong>English Summary:</strong>
                    {row.summary_en || "N/A"}
                  </Typography.Paragraph>
                </div>
              ),
            }}
            columns={[
              {
                title: "标题",
                render: (_, row) => (
                  <div>
                    <a href={row.link} target="_blank" rel="noreferrer">
                      {row.title_zh || row.title || "(无标题)"}
                    </a>
                    <div style={{ color: "#6b7280", marginTop: 4 }}>{row.title_en || row.title || ""}</div>
                  </div>
                ),
              },
              { title: "来源", dataIndex: "source_name", width: 170 },
              { title: "分组", dataIndex: "group_name", width: 120, render: (v) => <Tag color="green">{v}</Tag> },
              {
                title: "AI",
                dataIndex: "ai_status",
                width: 100,
                render: (v) => <Tag color={v === "success" ? "green" : v === "failed" ? "red" : "gold"}>{v}</Tag>,
              },
              { title: "发布时间", dataIndex: "published_at", width: 240, ellipsis: true },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );

  const managePanel = (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={8} style={{ display: "flex" }}>
        <Card className="glass" title="创建分组" style={{ width: "100%" }}>
          <Form form={groupForm} onFinish={addGroup} layout="vertical">
            <Form.Item label="分组名称" name="name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Button type="primary" htmlType="submit" block>
              新增分组
            </Button>
          </Form>
        </Card>
      </Col>
      <Col xs={24} lg={16} style={{ display: "flex" }}>
        <Card className="glass" title="添加 RSS 源" style={{ width: "100%" }}>
          <Form form={sourceForm} onFinish={addSource} layout="vertical">
            <Row gutter={12}>
              <Col xs={24} md={8}>
                <Form.Item label="名称" name="name" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={24} md={10}>
                <Form.Item label="URL" name="url" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item label="分组" name="group_id">
                  <Select allowClear options={groups.map((g) => ({ label: g.name, value: g.id }))} />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item label="启用" name="enabled" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
            <Button type="primary" htmlType="submit">
              保存源
            </Button>
          </Form>
        </Card>
      </Col>

      <Col span={24}>
        <Card
          className="glass"
          title="订阅源列表"
          extra={
            <Space>
              <Button onClick={exportOpml}>导出 OPML</Button>
              <input id="opml-import-input" type="file" accept=".opml,text/xml,application/xml" style={{ display: "none" }} onChange={importOpml} />
              <label htmlFor="opml-import-input">
                <Button type="primary">导入 OPML</Button>
              </label>
            </Space>
          }
        >
          <Table
            rowKey="id"
            dataSource={sources}
            pagination={{ pageSize: 8 }}
            columns={[
              { title: "ID", dataIndex: "id", width: 60 },
              { title: "名称", dataIndex: "name" },
              { title: "URL", dataIndex: "url", ellipsis: true },
              {
                title: "分组",
                dataIndex: "group_id",
                render: (id) => {
                  const group = groups.find((g) => g.id === id);
                  return <Tag color="green">{group ? group.name : "未分组"}</Tag>;
                },
              },
              {
                title: "状态",
                dataIndex: "enabled",
                render: (v) => <Tag color={v ? "blue" : "default"}>{v ? "启用" : "停用"}</Tag>,
              },
              {
                title: "操作",
                render: (_, row) => (
                  <Space>
                    <Button
                      size="small"
                      onClick={async () => {
                        await client.post(`/api/rss/sources/${row.id}/test`);
                        message.success("拉取完成");
                        loadAll();
                      }}
                    >
                      拉取
                    </Button>
                    <Button
                      size="small"
                      danger
                      onClick={async () => {
                        await client.delete(`/api/rss/sources/${row.id}`);
                        loadMeta();
                      }}
                    >
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

  return (
    <div>
      <Card className="glass" style={{ marginBottom: 16 }}>
        <Space style={{ width: "100%", justifyContent: "space-between", flexWrap: "wrap" }}>
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>
              RSS Workspace
            </Typography.Title>
            <Typography.Text type="secondary">管理订阅，也可以直接作为阅读器使用</Typography.Text>
          </div>
          <Segmented
            value={mode}
            onChange={setMode}
            options={[
              { label: "阅读器", value: "reader" },
              { label: "源管理", value: "manage" },
            ]}
          />
        </Space>
      </Card>

      {mode === "reader" ? readerPanel : managePanel}
    </div>
  );
}
