import { Button, Card, Col, Row, Table, Tag } from "antd";
import { useEffect, useState } from "react";
import client from "../services/api";

export default function LogsPage() {
  const [pullLogs, setPullLogs] = useState([]);
  const [sendLogs, setSendLogs] = useState([]);

  const load = async () => {
    const [p, s] = await Promise.all([client.get("/api/logs/pull"), client.get("/api/logs/send")]);
    setPullLogs(p.data);
    setSendLogs(s.data);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Button onClick={load}>刷新日志</Button>
      </Col>
      <Col xs={24} lg={12}>
        <Card className="glass" title="拉取日志">
          <Table
            rowKey="id"
            dataSource={pullLogs}
            pagination={{ pageSize: 6 }}
            columns={[
              { title: "源ID", dataIndex: "source_id" },
              { title: "状态", dataIndex: "status", render: (v) => <Tag color={v === "success" ? "green" : "red"}>{v}</Tag> },
              { title: "信息", dataIndex: "message", ellipsis: true },
            ]}
          />
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card className="glass" title="发送日志">
          <Table
            rowKey="id"
            dataSource={sendLogs}
            pagination={{ pageSize: 6 }}
            columns={[
              { title: "任务ID", dataIndex: "task_id" },
              { title: "收件人", dataIndex: "recipient_email", ellipsis: true },
              { title: "状态", dataIndex: "status", render: (v) => <Tag color={v === "success" ? "green" : "red"}>{v}</Tag> },
              { title: "信息", dataIndex: "message", ellipsis: true },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );
}
